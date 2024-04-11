package main

import (
	"bufio"
	"context"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/bedrockruntime"
)

const defaultRegion = "us-east-1"
const claude3_sonnet = "anthropic.claude-3-sonnet-20240229-v1:0"
const claude3_haiku = "anthropic.claude-3-haiku-20240307-v1:0"

var brc *bedrockruntime.Client

func init() {
	region := os.Getenv("AWS_REGION")
	if region == "" {
		region = defaultRegion
	}

	cfg, err := config.LoadDefaultConfig(context.Background(), config.WithRegion(region))
	if err != nil {
		log.Fatal(err)
	}

	brc = bedrockruntime.NewFromConfig(cfg)
}

var verbose *bool

func main() {
	verbose = flag.Bool("verbose", false, "setting to true will log messages being exchanged with LLM")
	filePathFlag := flag.String("img", "", "Please specify the file path. Example: -img <FilePath>")
	flag.Parse()

	reader := bufio.NewReader(os.Stdin)

	fmt.Print("\nEnter your message: ")
	input, _ := reader.ReadString('\n')
	input = strings.TrimSpace(input)

	var response string
	var err error

	if *filePathFlag != "" {
		filePath := *filePathFlag
		response, err = sendWithImage(input, filePath)
	} else {
		msg := fmt.Sprintf(claudePromptFormat, input)
		response, err = send(msg)
	}

	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("\n--- Response ---")
	fmt.Println(response)
}

const claudePromptFormat = "\n\nHuman: %s\n\nAssistant:"

func send(msg string) (string, error) {
	if *verbose {
		fmt.Println("[sending message]", msg)
	}

	var payloadBytes []byte
	var err error

	payload := Request{Messages: []Message{Message{Role: "user", Content: msg}}, MaxTokens: 4096, Version: "bedrock-2023-05-31"}
	payloadBytes, err = json.Marshal(payload)
	if err != nil {
		return "", err
	}

	output, err := brc.InvokeModel(context.Background(), &bedrockruntime.InvokeModelInput{
		Body:        payloadBytes,
		ModelId:     aws.String(claude3_sonnet),
		ContentType: aws.String("application/json"),
	})

	if err != nil {
		return "", err
	}

	return string(output.Body), nil
}

func sendWithImage(msg string, filePath string) (string, error) {
	if *verbose {
		fmt.Println("[sending message with image]", msg)
	}

	base64Image, err := encodeImageToBase64(filePath)
	if err != nil {
		return "", err
	}

	contentImage := ContentImg{
		Type: "image",
		Source: &Source{
			Type:      "base64",
			MediaType: "image/jpeg",
			Data:      base64Image,
		},
	}

	contentText := ContentImg{
		Type: "text",
		Text: msg,
	}

	message := MessageImg{
		Role:    "user",
		Content: []ContentImg{contentImage, contentText},
	}

	request := RequestImg{
		AnthropicVersion: "bedrock-2023-05-31",
		MaxTokens:        4096,
		Messages:         []MessageImg{message},
	}

	payloadBytes, err := json.Marshal(request)
	if err != nil {
		return "", err
	}

	output, err := brc.InvokeModel(context.Background(), &bedrockruntime.InvokeModelInput{
		Body:        payloadBytes,
		ModelId:     aws.String(claude3_sonnet),
		ContentType: aws.String("application/json"),
	})

	if err != nil {
		return "", err
	}

	return string(output.Body), nil

}

func encodeImageToBase64(filePath string) (string, error) {
	image, err := os.ReadFile(filePath)
	if err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(image), nil
}

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type Request struct {
	Messages      []Message `json:"messages"`
	MaxTokens     int       `json:"max_tokens"`
	Temperature   float64   `json:"temperature,omitempty"`
	TopP          float64   `json:"top_p,omitempty"`
	TopK          int       `json:"top_k,omitempty"`
	StopSequences []string  `json:"stop_sequences,omitempty"`
	Version       string    `json:"anthropic_version"`
}

type Response struct {
	Completion string `json:"completion"`
}

type ContentImg struct {
	Type   string  `json:"type"`
	Text   string  `json:"text,omitempty"`
	Source *Source `json:"source,omitempty"`
}

type Source struct {
	Type      string `json:"type"`
	MediaType string `json:"media_type"`
	Data      string `json:"data"`
}

type MessageImg struct {
	Role    string       `json:"role"`
	Content []ContentImg `json:"content"`
}

type RequestImg struct {
	AnthropicVersion string       `json:"anthropic_version"`
	MaxTokens        int          `json:"max_tokens"`
	System           string       `json:"system,omitempty"`
	Messages         []MessageImg `json:"messages"`
}
