package main

import (
	"os"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"

	"fmt"
	"log"
)

const dateFormat = "2006-01-02_15:04:05"

func main() {
	config := loadConfig("config.json")
	folder := config.Customer + "/" + config.Env + "/" + config.ID

	start, _ := time.Parse(dateFormat, config.StartDate)
	fmt.Println(start)
	end, _ := time.Parse(dateFormat, config.EndDate)
	fmt.Println(end)
	listObjects(config.Region, config.Bucket, folder, start, end)
}

func listObjects(region string, bucket string, folder string, start time.Time, end time.Time) {
	sess, err := session.NewSession(&aws.Config{
		Region: aws.String(region)},
	)

	svc := s3.New(sess)

	// Get the list of items
	resp, err := svc.ListObjects(&s3.ListObjectsInput{
		Bucket: aws.String(bucket),
		Prefix: aws.String(folder),
	})
	if err != nil {
		exitErrorf("Unable to list items in bucket %q, %v", bucket, err)
	}

	for _, item := range resp.Contents {
		time, _ := time.Parse(dateFormat, strings.TrimPrefix(*item.Key, folder+"/"))
		if inTimeSpan(start, end, time) {
			fmt.Println("Name:         ", *item.Key)
			fmt.Println("Last modified:", *item.LastModified)
			fmt.Println("Size:         ", *item.Size)
			fmt.Println("")
		}
	}

	fmt.Println("Found", len(resp.Contents), "items in bucket", bucket)
	fmt.Println("")
}

func downloadObject(filename string, region string, bucket string) {
	file, err := os.Create(filename)
	if err != nil {
		exitErrorf("Unable to open file %q, %v", err)
	}

	defer file.Close()

	sess, _ := session.NewSession(&aws.Config{
		Region: aws.String(region)},
	)

	downloader := s3manager.NewDownloader(sess)

	numBytes, downloadErr := downloader.Download(file,
		&s3.GetObjectInput{
			Bucket: aws.String(bucket),
			Key:    aws.String(filename),
		})

	if downloadErr != nil {
		log.Fatalf("Unable to download item %q, %v", filename, err)
	}

	fmt.Println("Downloaded", file.Name(), numBytes, "bytes")
}

func inTimeSpan(start, end, check time.Time) bool {
	return check.After(start) && check.Before(end)
}

func exitErrorf(msg string, args ...interface{}) {
	fmt.Fprintf(os.Stderr, msg+"\n", args...)
	os.Exit(1)
}
