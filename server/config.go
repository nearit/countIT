package main

import (
	"encoding/json"
	"fmt"
	"os"
)

// Config maps a config file to struct
type Config struct {
	Bucket    string `json:"bucket_name"`
	Region    string `json:"region"`
	Env       string `json:"env"`
	Customer  string `json:"customer"`
	ID        string `json:"id"`
	StartDate string `json:"start_date"`
	EndDate   string `json:"end_date"`
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
