package main

import (
	"encoding/json"
	"os"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"

	"fmt"
	"log"
)

// Config maps a config file to struct
type Config struct {
	Bucket   string `json:"bucket_name"`
	Region   string `json:"region"`
	Env      string `json:"env"`
	Customer string `json:"customer"`
	ID       string `json:"id"`
}

func main() {
	config := loadConfig("config.json")
	listObjects(config.Region, config.Bucket, config.Customer+"/"+config.Env+"/"+config.ID)
}

func loadConfig(filename string) Config {
	var config Config
	configFile, err := os.Open(filename)
	defer configFile.Close()
	if err != nil {
		fmt.Println(err.Error())
	}
	jsonParser := json.NewDecoder(configFile)
	jsonParser.Decode(&config)
	return config
}

func listObjects(region string, bucket string, folder string) {
	sess, err := session.NewSession(&aws.Config{
		Region: aws.String(region)},
	)

	// Create S3 service client
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
		fmt.Println("Name:         ", *item.Key)
		fmt.Println("Last modified:", *item.LastModified)
		fmt.Println("Size:         ", *item.Size)
		fmt.Println("Storage class:", *item.StorageClass)
		fmt.Println("")
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

	// 2) Create an AWS session
	sess, _ := session.NewSession(&aws.Config{
		Region: aws.String(region)},
	)

	// 3) Create a new AWS S3 downloader
	downloader := s3manager.NewDownloader(sess)

	// 4) Download the item from the bucket. If an error occurs, log it and exit. Otherwise, notify the user that the download succeeded.
	numBytes, err := downloader.Download(file,
		&s3.GetObjectInput{
			Bucket: aws.String(bucket),
			Key:    aws.String(filename),
		})

	if err != nil {
		log.Fatalf("Unable to download item %q, %v", filename, err)
	}

	fmt.Println("Downloaded", file.Name(), numBytes, "bytes")
}

func exitErrorf(msg string, args ...interface{}) {
	fmt.Fprintf(os.Stderr, msg+"\n", args...)
	os.Exit(1)
}
