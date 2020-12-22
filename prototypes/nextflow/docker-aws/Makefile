nextflow-run:
	nextflow run docker.nf \
		-work-dir s3://aviris-data/nextflow-workdir-test/ \
		-bucket-dir s3://aviris-data/nextflow-bucketdir-test/ \
		-with-trace -with-timeline -with-dag -with-report \
		--event '{"msg": "workflow run"}'

nextflow-run-activator:
	nextflow run docker.nf \
		-work-dir s3://aviris-data/nextflow-workdir-test/ \
		-bucket-dir s3://aviris-data/nextflow-bucketdir-test/ \
		-with-trace -with-timeline -with-dag -with-report \
		--event '{"msg": "activator run"}' --event_type 'activator'

nextflow-run-processor:
	nextflow run docker.nf \
		-work-dir s3://aviris-data/nextflow-workdir-test/ \
		-bucket-dir s3://aviris-data/nextflow-bucketdir-test/ \
		-with-trace -with-timeline -with-dag -with-report \
		--event '{"msg": "processor run"}' --event_type 'processor'

nextflow-resume:
	nextflow run docker.nf \
		-work-dir s3://aviris-data/nextflow-workdir-test/ \
		-bucket-dir s3://aviris-data/nextflow-bucketdir-test/ \
		-with-trace -with-timeline -with-dag -with-report -latest -resume \
		--event '{"msg": "workflow run"}'

nextflow-cleanup: 
	rm -rf .nextflow* docker.dot* docker.html* work dag.dot* report.html* timeline.html* trace.txt*
