nextflow-run:
	nextflow run docker.nf -with-report docker.html -with-dag docker.dot --event '{"msg": "workflow run"}'

nextflow-run-activator:
	nextflow run docker.nf -with-report docker.html -with-dag docker.dot --event '{"msg": "activator run"}' --event_type 'activator'

nextflow-run-processor:
	nextflow run docker.nf -with-report docker.html -with-dag docker.dot --event '{"msg": "processor run"}' --event_type 'processor'

nextflow-cleanup: 
	rm -rf .nextflow* docker.dot* docker.html* work dag.dot* report.html* timeline.html* trace.txt*
