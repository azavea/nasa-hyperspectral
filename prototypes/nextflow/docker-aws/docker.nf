// https://www.nextflow.io/docs/latest/dsl2.html
nextflow.enable.dsl=2

process activator { 
  container '513167130603.dkr.ecr.us-east-1.amazonaws.com/nasa-hsi-v2-nextflow:latest' 

  input:
  val event

  output:
  file 'activator_event.json'

  shell:
  '''
   python /workdir/activator.py '!{event}'
  '''
}

process processor {
  container '513167130603.dkr.ecr.us-east-1.amazonaws.com/nasa-hsi-v2-nextflow:latest'

  input:
  val event_file

  output:
  file 'processor_event.json'

  shell:
  '''
  python /workdir/processor.py '!{event_file}'
  '''
}

workflow {
  // variables init
  params.event = ''
  params.event_type = ''

  event_ch = Channel.of(params.event)
  
  // describe different workflow modes
  if(params.event_type == 'activator') {
    activator(event_ch)
    activator.out.map(file -> file.text).view()
  } else if (params.event_type == 'processor') {
    processor(event_ch)
    processor.out.map(file -> file.text).view()
  } else {
    activator(event_ch)
    processor_input = activator.out.map(file -> file.text)
    processor(processor_input)
    processor.out.map(file -> file.text).view()
  }
}
