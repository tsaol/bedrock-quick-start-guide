

## 目录说面

这个目录包含了使用 AWS Bedrock 服务的 Golang 示例代码。以下是对每个文件的简要说明:

### bedrock.go
这个文件演示了如何使用 AWS SDK for Go (v2) 创建一个 Amazon Bedrock 客户端,并列出账户中指定区域内可用的基础模型。它使用共享凭证和配置文件中的默认设置。

### bedrock_101.go
这个文件展示了一个简单的聊天应用示例。它使用 AWS Bedrock Runtime 服务与 Claude3 模型进行交互。用户可以通过命令行输入消息,程序将消息发送给模型并打印出响应。

主要功能:

与 Claude3 模型 (sonnet 或 haiku 版本) 进行交互
通过命令行参数控制是否打印详细消息
封装了与 Bedrock Runtime 服务通信的逻辑

### bedrock_301
这个文件在 bedrock_101.go 的基础上增加了发送图像的功能。用户可以通过命令行参数指定图像文件路径,程序会将图像编码为 base64 格式,并与文本消息一起发送给模型。

主要功能:

支持发送图像给 Claude3 模型
图像需要转换为 base64 编码
使用特定的请求格式来发送包含图像和文本的消息
这些示例代码展示了如何使用 AWS Bedrock 服务的 Golang SDK 与不同的模型进行交互,并提供了逐步构建聊天应用的过程。你可以以这些代码为基础,根据需求进行修改和扩展,以构建自己的应用。

## 使用说明

`aws-sdk-go-v2` is the v2 AWS SDK for the Go programming language.

**The v2 SDK requires a minimum version of Go 1.20.
**

reference : https://pkg.go.dev/github.com/aws/aws-sdk-go-v2#section-readme


1. 初始化一个新的 Go 项目：


```
go mod init bedrock
```

这将在你的项目目录中创建一个名为 go.mod 的文件。

2. 运行以下命令安装所需的依赖项：

```
go get github.com/aws/aws-sdk-go-v2/aws
go get github.com/aws/aws-sdk-go-v2/config
go get github.com/aws/aws-sdk-go-v2/service/bedrockruntime
go get github.com/aws/aws-sdk-go-v2/service/bedrockruntime/types
```


3. 运行
```
go run bedrock.go
```