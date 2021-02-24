package main

import (
	"fmt"
	"testing"
	"net/http"
	"io"
	"mime/multipart"
	"bytes"
	"os"
	"os/exec"
	"strings"
)

func TestGetSentence(*testing.T) {
	resp, err := http.Get("http://localhost:8080/sentence/get")
	if err != nil {
		panic(err)
	}
	bytes := make([]byte, 256)
	_, err = resp.Body.Read(bytes)
	if err != nil && err != io.EOF {
		panic(err)
	}
	fmt.Println("Sentence recieved: " + string(bytes))
}

func TestStoreVideo(*testing.T) {
	testFile, err := os.Open("../testing/test.mov")
	if err != nil && os.IsNotExist(err) {
		panic("Please supply a test video file 'test.mov' in ../testing")
	}
	defer func() {
		err := testFile.Close()
		if err != nil {
			panic(err)
		}
	}()
	var b bytes.Buffer
	w := multipart.NewWriter(&b)
	fw, err := w.CreateFormField("userID")
	if _, err = io.Copy(fw, strings.NewReader("testID")); err != nil {
		panic(err)
	}
	fw, err = w.CreateFormField("sentence")
	if _, err = io.Copy(fw, strings.NewReader("This is a test sentence.")); err != nil {
		panic(err)
	}
	fw, err = w.CreateFormFile("videoFile", testFile.Name())
	if err != nil {
		panic(err)
	}
	if _, err = io.Copy(fw, testFile); err != nil {
		panic(err)
	}
	w.Close()
	req, err := http.NewRequest("POST", "http://localhost:8080/data/upload", &b)
	if err != nil {
		panic(err)
	}
	req.Header.Set("Content-Type", w.FormDataContentType())
	client := &http.Client{}
	client.Do(req)
	fmt.Println("Sent test data --- checking for integrity")
	fmt.Println("Difference between expected metadata file and actual metadata file:")
	metadataCheckCmd := exec.Command("diff", "-a", "--text", "../testing/metadata-1.txt", "../data/testID/33eb0576bd8ecb5317c08dfaa4c3c2853ac740b23c248ef65959c4fe12eca4cf/metadata-1.txt")
	metadataCheckCmd.Run()
	fmt.Println("Difference between expected video file and actual video file:")
	videoCheckCmd := exec.Command("diff", "-a", "--text", "../testing/test.mov", "../data/testID/33eb0576bd8ecb5317c08dfaa4c3c2853ac740b23c248ef65959c4fe12eca4cf/test.mov")
	videoCheckCmd.Run()
	fmt.Println("Cleaning test directories")
	rmAllCmd := exec.Command("rm", "../data/testID", "-r")
	rmAllCmd.Run()
}