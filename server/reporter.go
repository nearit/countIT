package main

import (
	"fmt"
	"log"
	"strconv"

	"github.com/tealeg/xlsx"
)

var file *xlsx.File
var sheet *xlsx.Sheet
var row *xlsx.Row
var cell *xlsx.Cell
var col *xlsx.Col
var err error

func initReport() {
	file = xlsx.NewFile()
	sheetName := fmt.Sprintf("%v - %v", config.StartDate[:10], config.EndDate[:10])
	sheet, err = file.AddSheet(sheetName)
	if err != nil {
		fmt.Printf(err.Error())
	}
	row = sheet.AddRow()
	row.AddCell().SetString("Timestamp")
	row.AddCell().SetString("Count")
}

func addRow(timestamp string, count int) {
	row = sheet.AddRow()
	cell = row.AddCell()
	cell.Value = timestamp
	cell = row.AddCell()
	cell.Value = strconv.Itoa(count)
}

func generateReport() {
	fileName := fmt.Sprintf(config.Customer + "_" + config.ID)
	err = file.Save(fileName + ".xlsx")
	if err != nil {
		log.Fatalf("Unable to save report, %v", err)
	}
}
