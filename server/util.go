package main

import (
	"log"
	"time"
)

const dateFormat = "2006-01-02_15:04:05"

func parseDate(date string) time.Time {
	parsed, err := time.Parse(dateFormat, date)
	if err != nil {
		log.Fatalf("Unable to parse date, %q %v", date, err)
	}
	return parsed
}
