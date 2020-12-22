params.event  = '{"msg": "text"}'
event_ch = Channel.of(params.event)

process activator { 
  container '513167130603.dkr.ecr.us-east-1.amazonaws.com/nasa-hsi-v2-nextflow:latest' 

  input:
  val event from event_ch

  output:
  file 'activator_event.json' into processor_ch

  shell:
  '''
   python /workdir/activator.py '!{event}'
  '''
}

process processor {
  container '513167130603.dkr.ecr.us-east-1.amazonaws.com/nasa-hsi-v2-nextflow:latest'

  input:
  file event_file from processor_ch

  output:
  file 'processor_event.json' into result

  shell:
  '''
  python /workdir/processor.py "`cat !{event_file}`"
  '''
}

result.view { it }
