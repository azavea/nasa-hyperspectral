nextflow-run:
	nextflow run docker.nf -with-trace -with-timeline -with-dag -with-report --event '{"msg": "workflow run"}'

nextflow-run-activator:
	nextflow run docker.nf -with-trace -with-timeline -with-dag -with-report --event '{"msg": "activator run"}' --event_type 'activator'

nextflow-run-processor:
	nextflow run docker.nf -with-trace -with-timeline -with-dag -with-report --event '{"msg": "processor run"}' --event_type 'processor'

nextflow-cleanup: 
	rm -rf .nextflow* docker.dot* docker.html* work dag.dot* report.html* timeline.html* trace.txt*
