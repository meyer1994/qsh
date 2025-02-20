.PHONY: clean deploy


clean:
	rm -rf dist
	rm -rf cdk.out
	rm -f requirements.txt
	rm -f package.zip


requirements.txt:
	uv export \
		--frozen \
		--no-dev \
		--no-editable \
		--output-file requirements.txt


package.zip: requirements.txt
	mkdir -pv dist
	uv pip install \
		--no-installer-metadata \
		--no-compile-bytecode \
		--python-version '3.13' \
		--python-platform 'x86_64-manylinux2014' \
		--requirements 'requirements.txt' \
		--target './dist'
	cd dist && zip -r ../package.zip .
	zip -r package.zip handler.py


deploy: package.zip
	npx aws-cdk deploy --verbose
