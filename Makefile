.PHONY: build deploy clean

build:
	poetry export -f requirements.txt --only main --without-hashes > requirements.txt
	sh ./scripts/build-layer.sh
	poetry run sam build

deploy:
	pipx run aws-sam-cli deploy --guided

clean:
	rm -rf .aws-sam
	rm -rf dependencies
	rm -f requirements.txt
