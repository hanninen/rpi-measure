package:
	sam package --template-file  template.yaml --s3-bucket hanninen-sam-deploy --output-template-file packaged.yaml

deploy:
	cfn-lint packaged.yaml
	sam deploy --template-file packaged.yaml --stack-name rpi-measure --capabilities CAPABILITY_IAM

install: package deploy
