
aws-sdk-go-v2 is the v2 AWS SDK for the Go programming language.

The v2 SDK requires a minimum version of Go 1.20.


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

