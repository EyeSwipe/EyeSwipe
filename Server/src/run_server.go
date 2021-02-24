package main

import (
	"net/http"
	"os"
	"log"
	"io/fs"
)

func main() {
	sentManager := &SentenceManager{}
	sentManager.loadSentences()

	info, err := os.Stat("../data")
	if os.IsNotExist(err) {
		os.Mkdir("../data", fs.ModeDir)
		err = nil
	}
	if (info != nil) && (!info.IsDir()) {
		panic("Error: file 'data' exists and is not a directory")
	} 
	if err != nil {
		panic(err)
	}

	http.HandleFunc("/sentence/get", sentManager.sentenceGetHandler)
	http.HandleFunc("/data/upload", videoUploadHandler)

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		return
	})

	log.Fatal(http.ListenAndServe(":8080", nil))
}
