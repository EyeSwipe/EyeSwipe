package main

import (
	"net/http"
)

func (sentManager *SentenceManager) sentenceGetHandler(w http.ResponseWriter, r *http.Request) {
	sentence := sentManager.getSentence()
	w.Write([]byte(sentence))
}

func videoUploadHandler(w http.ResponseWriter, r *http.Request) {
	err := r.ParseMultipartForm((1 << 20) * 100)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("400 - Failed to parse form: " + err.Error()))
		return
	}
	stringMap := r.MultipartForm.Value
	fileMap := r.MultipartForm.File
	userID, ok := stringMap["userID"]
	if !ok {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("400 - Field 'userID' not included in video upload"))
		return
	}
	_, ok = stringMap["sentence"]
	if !ok {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("400 - Field 'sentence' not included in video upload"))
		return
	}
	videoFileHeader, ok := fileMap["videoFile"]
	if !ok {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("400 - Field 'videoFile' not included in video upload"))
		return
	}
	videoFile, err := videoFileHeader[0].Open()
	defer func() {
		if err := videoFile.Close(); err != nil {
			panic(err)
		}
	}()
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("400 - Video file failed to open"))
		return
	}
	storeVideo(userID[0], stringMap, &videoFile)
	return
}