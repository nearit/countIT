package main

import (
	"log"
	"time"
)

const dateFormat = "2006-01-02 15:04:05 +0700"

func parseDateWithFormat(date, format string) time.Time {
	parsed, err := time.Parse(format, date)
	if err != nil {
		log.Fatalf("Unable to parse date, %q %v", date, err)
	}
	return parsed
}

func parseDate(date string) time.Time {
	parsed, err := time.Parse(dateFormat, date)
	if err != nil {
		log.Fatalf("Unable to parse date, %q %v", date, err)
	}
	return parsed
}

func inTimeSpan(start, end, check time.Time) bool {
	return check.After(start) && check.Before(end)
}
