package main

import (
	"bytes"
	"encoding/json"

	"io"
	"os"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"

	"fmt"
)

// Trackings contains total count and a list of detections
type Trackings struct {
	Count   int         `json:"count"`
	Devices []Detection `json:"devices"`
}

// Detection contains RSSI, MAC address and Manufaturer detected
type Detection struct {
	RSSI         float32 `json:"rssi"`
	MAC          string  `json:"mac"`
	Manufacturer string  `json:"Manufacturer"`
}

var config Config
var folder string

func main() {
	config = loadConfig("config.json")
	folder = config.Customer + "/" + config.Env + "/" + config.ID

	listObjects()
}

func listObjects() {
	fmt.Println("Fetching detections from", config.StartDate, "to", config.EndDate)

	start := parseDate(config.StartDate)
	end := parseDate(config.EndDate)

	sess, err := session.NewSession(&aws.Config{
		Region: aws.String(config.Region)},
	)

	svc := s3.New(sess)

	resp, err := svc.ListObjects(&s3.ListObjectsInput{
		Bucket: aws.String(config.Bucket),
		Prefix: aws.String(folder),
	})
	if err != nil {
		exitErrorf("Unable to list items in bucket %q, %v", config.Bucket, err)
	}

	initReport()
	for _, item := range resp.Contents {
		filename := strings.TrimPrefix(*item.Key, folder+"/")
		time := parseDate(filename)
		if inTimeSpan(start, end, time) {
			trackings := readFile(*item.Key)
			addRow(filename, trackings.Count)
		}
	}
	generateReport()
}

func readFile(filename string) Trackings {
	sess := session.New()
	svc := s3.New(sess, aws.NewConfig().WithRegion(config.Region))

	results, err := svc.GetObject(&s3.GetObjectInput{
		Bucket: aws.String(config.Bucket),
		Key:    aws.String(filename),
	})
	if err != nil {
		//log.Fatalf("Unable to get object %q from bucket %v", filename, err)
		fmt.Printf("Unable to get object %q from bucket %v", filename, err)
	}

	defer results.Body.Close()

	buf := bytes.NewBuffer(nil)
	if _, err := io.Copy(buf, results.Body); err != nil {
		//log.Fatalf("Unable to bufferize results, %v", err)
		fmt.Printf("Unable to bufferize results, %v", err)
	}

	var trackings Trackings
	jsonParser := json.NewDecoder(buf)
	jsonParser.Decode(&trackings)

	return trackings
}

func exitErrorf(msg string, args ...interface{}) {
	fmt.Fprintf(os.Stderr, msg+"\n", args...)
	os.Exit(1)
}
