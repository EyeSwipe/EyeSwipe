package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"math/rand"
	"net/http"
	"os"
	"log"
	"strings"
	"sync"
	"time"

	"github.com/pkg/errors"
)

// We've made the file a symbolic link so that paths can be used properly
// once compiled.
const sentencesFile = "sentences-link.txt"

const stateSavePath = "server-state.json"

func main() {
	// TODO: Add in storage associated information with users upon registration
	// TODO: Add a way to receive videos and the associated metadata

	ctx := initialize()

	checkSave := func() error {
		return ctx.saveAllocated()
	}

	go func() {
		if err := waitExec(checkSave, 100, ctx.changeTrigger); err != nil {
			log.Fatal(err)
		}
	}()

	handleWithContext := func(handler f(*MainContext, http.ResponseWriter, http.Request)) func(http.ResponseWriter, *http.Request) {
		return func(w http.ResponseWriter, r *http.Request) {
			handler(ctx, w, f)
		}
	}

	http.HandleFunc("/sentence/get", handleWithContext(sentenceAllocHandler))
	http.HandleFunc("/user/new", handleWithContext(newUserHandler))

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		return
	})

	log.Fatal(http.ListenAndServe(":8080", nil))
}

// MainContext allows any function to access the components they need from
// `main()`.  For information on the generation of these fields, see the
// comments in `initialize()`.
type MainContext struct {
	// excluded because we'll read it from elsewhere
	sentences []string `json:"-"`

	// controls access to `allocated`, `unalloc`, and `users`
	mux sync.Mutex `json:"-"`

	allocated map[int]*sentenceInfo
	unalloc   []int

	users []*userInfo

	// shared channel to indicate when to save the server state. This is
	// a buffered channel with size 1
	//
	// boolean value indicates whether to write both `allocated` and
	// `users`, or just `users`. Writes to both if true.
	writeTrigger chan struct{} `json:"-"`
}

// Simple set of information for each sentence that has already been given
// to a user for training data.
type sentenceInfo struct {
	// Equal to the index of the sentence in the total list of sentences
	ID     int
	Text   string
	UserID int
}

// Bits of information for a user
type userInfo struct {
	ID          int
	Name        string
	DeviceName  string
	SentenceIDs []int
}

// Generates the context to be handled by `main`
//
// There is plenty of information on exactly how this is done within the
// function itself
//
// Panic conditions:
// * Failure to resolve sym-link at 'sentences-link.txt'
// * ^ File pointed to by sym-link does not exist
// * Failure to parse JSON at 'allocated.json' -- IFF it exists
// * There is a UserID greater than the total number of users
// * ID to get sentenceInfo doesn't match sentenceInfo.ID
// * ^ Sentence by ID doesn't match sentenceInfo.Text with that ID
func initialize() (ctx *MainContext) {
	ctx = new(MainContext)
	ctx.writeTrigger = make(chan struct{}, 1)

	// simple helper function to improve readability
	check := func(err error) {
		if err != nil {
			panic(err)
		}
	}

	// load the list of sentences
	//
	// Note: Previously had:
	/*
		filePath, err := os.Readlink(sentencesFile)
		check(err)

		// Read the file and split it into sentences
		bs, err := ioutil.ReadFile(filePath)
		check(err)

		// Each line is a sentence and each sentence on a single line
		ctx.sentences = strings.Split(string(bs), "\n")
	*/
	bytes, err := ioutil.ReadFile(sentencesFile)
	check(err)

	ctx.sentences = strings.Split(string(bytes), "\n")

	// if os.Stat returns non-nil error, the file exists
	if _, err := os.Stat(stateSavePath); err != nil {
		str, err := ioutil.ReadFile(stateSavePath)
		check(err)

		err = json.Unmarshal(str, ctx)
		check(err)

		// check for certain possible errors
		for id, info := range ctx.allocated {
			if info.ID != id {
				s := fmt.Sprintf("Listing for SentenceID %d has ID %d", id, info.ID)
				panic(s)
			}

			if info.Text != ctx.sentences[id] {
				s := fmt.Sprintf("Sentence text mismatch for ID %d: info: %q, list: %q",
					info.ID,
					info.Text[:10]+"...",
					ctx.sentences[info.ID][:10]+"...")
				panic(s)
			}
		}

		for id, info := range ctx.users {
			if info.ID != id {
				s := fmt.Sprintf("Listing for UserID %d has ID %d", id, info.ID)
				panic(s)
			}

			for i, sID := range info.SentenceIDs {
				s, ok := ctx.allocated[sID]
				if !ok {
					s := fmt.Sprintf("UserID %d has SentenceID %d, but sentence has not been allocated",
						id, sID)
					panic(s)
				}

				if s.UserID != id {
					s := fmt.Sprintf("UserID %d has SentenceID %d, but sentence lists UserID %d as owner",
						id, sID, s.UserID)
					panic(s)
				}
			}
		}

		return ctx
	}

	// else, we need to generate a blank instance of `ctx`.
	//
	// The only other fields that need generating if there hasn't been any
	// activity yet are `allocated` and `unalloc`. The former simply needs
	// to be created, and the latter is just a list from 0 to
	// len(sentences)-1
	ctx.allocated = make(map[int]*sentenceInfo)
	ctx.unalloc = make([]int, len(ctx.sentences))
	for i := range ctx.unalloc {
		ctx.unalloc[i] = i
	}

	return ctx
}

type NoMoreSentencesError int

func (e NoMoreSentencesError) Error() string {
	return fmt.Sprintf("No more unallocated sentences. All (%d) in use.", int(e))
}

// Provides a new sentence for a user. Note: Is not thread-safe. Must be
// called from the thread holding ctx.mux
//
// It will only return error if we've run out of sentences. That error
// will be type `NoMoreSentencesError`.
//
// Assumes that the given userID is already present
func (ctx *MainContext) getAndAllocate(userID int) (*sentenceInfo, error) {
	if len(ctx.unalloc) == 0 {
		return nil, NoMoreSentencesError(len(ctx.sentences))
	}

	uIndex := rand.Intn(len(ctx.unalloc))
	index := ctx.unalloc[uIndex]

	info := sentenceInfo{
		ID:     index,
		Text:   ctx.sentences[index],
		UserID: userID,
	}

	ctx.allocated[index] = &info

	// remove `index` from unallocated
	copy(ctx.unalloc[uIndex:], ctx.unalloc[uIndex+1:])
	ctx.unalloc = ctx.unalloc[:len(ctx.unalloc)-1]

	// Signal that we've made a change.
	//
	// This shouldn't block because we made the channel with capacity and
	// it's constantly emptied
	ctx.writeTrigger <- struct{}{}

	return &info, nil
}

// This function spawns other goroutines and returns its result (if it
// terminates) through the returned channel. The returned error will only
// be nil if `ctx.writeTrigger` is closed.
func (ctx *MainContext) listenWriteTrigger(delayMillis int) (result <-chan error) {
	var triggerMux sync.Mutex

	var waiting bool

	secondaryTrigger := make(chan struct{}, 1)

	result = make(chan error, 1)

	// This function handles multiple sequential write requests so that
	// `ctx.writeTrigger` will not block for long (if it ever blocks).
	//
	// In practice, this is likely not necessary, but it's a nice
	// precaution to build for peace of mind so that our code is
	// future-proof
	go func() {
		for {
			_, ok := <-ctx.writeTrigger
			if !ok {
				close(secondaryTrigger)
				return
			}

			var trigger bool

			func() {
				triggerMux.Lock()
				defer triggerMux.Unlock()

				trigger = !waiting

				waiting = true
			}()

			if trigger {
				secondaryTrigger <- struct{}{}
			}
		}
	}()

	go func() {
		for {
			_, ok := <-secondaryTrigger
			if !ok {
				returnCh <- nil
				return
			}

			func() {
				triggerMux.Lock()
				defer triggerMux.Unlock()

				waiting = false
			}()

			func() {
				if b {
					ctx.userMux.Lock()
					defer ctx.userMux.Unlock()
				}

				ctx.allocMux.Lock()
				defer ctx.allocMux.Unlock()

				str, err := json.MarshalIndent(ctx)
				if err != nil {
					result <- fmt.Errorf("Failed to marshal JSON of server state (MainContext): %v", err)
					return
				}

				if err := ioutil.WriteFile(stateSavaePath, str, os.ModePerm); err != nil {
					result <- fmt.Errorf("Failed to write server state to file: %v", err)
					return
				}
			}()

			time.Sleep(time.Duration(delayMillis) * time.Millisecond)
		}
	}()

	return
}

// Adds a user with the given name and devicename to the system, returning
// the userID
//
// Takes out a lock on ctx.userMux
func (ctx *MainContext) enrollUser(name, deviceName string) int {

	

	panic("unimplemented!")
}