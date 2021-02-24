package main

import (
	"io"
	"io/ioutil"
	"io/fs"
	"bufio"
	"strings"
	"mime/multipart"
	"crypto/sha256"
	"crypto/rand"
	"encoding/binary"
	"encoding/hex"
	"os"
	"strconv"
)

type SentenceManager struct {
	sentences []string
}

func (sentManager *SentenceManager) loadSentences() {
	bytes, err := ioutil.ReadFile("../../Sentences/sentences.txt")
	if err != nil {
		panic(err)
	}
	sentManager.sentences = strings.Split(string(bytes), "\n")
}

func (sentManager *SentenceManager) getSentence() string {
	if len(sentManager.sentences) == 0 {
		panic("Attempted to get sentence before loading sentences.txt")
	}
	randBytes := make([]byte, 8)
	_, err := rand.Read(randBytes)
	if err != nil {
		panic(err)
	}
	randInt := int(binary.BigEndian.Uint64(randBytes))
	if randInt < 0 {
		randInt = -randInt
	}
	index := randInt % len(sentManager.sentences)
	return sentManager.sentences[index]
}

func storeVideo(userID string, metadata map[string][]string, videoReadFile *multipart.File) {
	userDirectory := "../data/" + userID
	checkAndCreateDir(userDirectory)
	sentenceHash := sha256.Sum256([]byte(metadata["sentence"][0]))
	videoDirectory := userDirectory + "/" + hex.EncodeToString(sentenceHash[:])
	checkAndCreateDir(videoDirectory)
	files, _ := ioutil.ReadDir(videoDirectory)
	copyNum := strconv.Itoa((len(files) / 2) + 1)
	videoFileName := videoDirectory + "/" + copyNum + ".mov"
	videoWriteFile, err := os.OpenFile(videoFileName, os.O_RDWR|os.O_CREATE, 0755)
	if err != nil {
		panic(err)
	}
	defer func() {
		if err := videoWriteFile.Close(); err != nil {
			panic(err)
		}
	}()
	transferFile(videoReadFile, videoWriteFile)
	metadataFileName := videoDirectory + "/" + "metadata-" + copyNum + ".txt"
	metadataWriteFile, err := os.OpenFile(metadataFileName, os.O_RDWR|os.O_CREATE, 0755)
	if err != nil {
		panic(err)
	}
	defer func() {
		if err := metadataWriteFile.Close(); err != nil {
			panic(err)
		}
	}()
	for k, v := range metadata {
		_, err = metadataWriteFile.Write([]byte(k + " : " + v[0] + "\n"))
		if err != nil {
			panic(err)
		}
	}
}

func transferFile(sourceFile *multipart.File, targetFile *os.File) {
	r := bufio.NewReader(*sourceFile)
	w := bufio.NewWriter(targetFile)
	buf := make([]byte, 1024)
	for {
		n, err := r.Read(buf)
		if n == 0 {
			if err == io.EOF {
				break
			} else {
				panic(err)
			}
		} else {
			_, err = w.Write(buf[:n])
			if err != nil {
				panic(err)
			}
		}
	}
	if err := w.Flush(); err != nil {
		panic(err)
	}
}

func checkAndCreateDir(path string) {
	info, err := os.Stat(path)
	if os.IsNotExist(err) {
		os.Mkdir(path, fs.ModeDir)
		err = nil
	}
	if info != nil && !info.IsDir() {
		panic("File " + path + " exists and is not a directory")
	}
	if err != nil {
		panic(err)
	}
}