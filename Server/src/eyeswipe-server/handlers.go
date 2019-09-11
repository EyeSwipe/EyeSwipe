// This file stores the individual HTTP handlers used in 'main.go'
package main

import (
	"http"
	"strconv"
)

// HTTP handler for allocating sentences to a user
func sentenceAllocHandler(ctx *MainContext, w http.ResponseWriter, r *http.Request) {
	userIDString := r.FormValue("user")
	if userIDString == "" {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("400 - No user supplied in request query."))
		return
	}

	userID, err := strconv.Atoi(userIDString)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("400 - Malformed UserID."))
		return
	}

	// check userID
	if userID < 0 {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("400 - UserID outside of valid range."))
		return
	}

	var done bool
	ctx.mux.Lock()
	defer func() {
		if !done {
			ctx.mux.Unlock()
		}
	}()

	if userID >= len(ctx.users) {
		ctx.mux.Unlock()
		done = true

		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("400 - UserID outside of valid range."))
		return
	}

	info, err := ctx.getAndAllocate(userID)
	if err != nil {
		ctx.mux.Unlock()
		done = true

		w.WriteHeader(http.StatusInternalServerError)
		fmt.Fwritef(w, "500 - Failed to allocate new sentence: %v", err)
		return		
	}

	ctx.mux.Unlock()
	done = true

	if err := json.NewEncoder(w).Encode(info); err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("500 - Failed to encode sentence information"))
		return
	}
}

// HTTP handler for enrolling a new user
//
// Expects the form/query to have two fields filled: 'name', and 'devicename'
func newUserHandler(ctx *MainContext, w http.ResponseWriter, r *http.Request) {
	err := r.ParseForm()
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		fmt.Fprintf(w, "400 - Failed to parse form: %v", err)
		return
	}

	// r.Form is type url.Values, which is equal to type map[string][]string
	values := map[string][]string(r.Form)

	var name, deviceName string
	var ok bool

	if name, ok = values["name"]; !ok {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("400 - Request did not include form field 'name'"))
		return
	} else if devicename, ok = values["devicename"]; !ok {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("400 - Request did not include form field 'devicename'"))
		return
	}

	userID, err := ctx.enrollUser(name, deviceName)

	// send the user ID back
	w.Write([]byte(strconv.Itoa(userID)))
	return
}