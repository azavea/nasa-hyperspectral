// In this example we used the new Nextflow DSL
// https://www.nextflow.io/docs/latest/dsl2.html
nextflow.enable.dsl=2

process activator { 
  // all nextflow porcesses in this example would be containerized
  container '513167130603.dkr.ecr.us-east-1.amazonaws.com/nasa-hsi-v2-nextflow:latest' 
  // error strategy specification
  errorStrategy 'retry'
  maxErrors 5

  // process input argument
  input:
  val event

  // process output
  output:
  file 'activator_event.json'

  // process execution script
  shell:
  '''
   python /workdir/activator.py '!{event}'
  '''
}

process processor {
  // all nextflow porcesses in this example would be containerized
  container '513167130603.dkr.ecr.us-east-1.amazonaws.com/nasa-hsi-v2-nextflow:latest' 
  // error strategy specification
  errorStrategy 'retry'
  maxErrors 5

  // process input argument
  input:
  val event

  // process output
  output:
  file 'processor_event.json'

  // process execution script
  shell:
  '''
  python /workdir/processor.py '!{event}'
  '''
}

workflow {
  // variables init
  params.event = ''
  params.event_type = ''

  // input events channel definition
  event_ch = Channel.of(params.event)
  
  // describe different workflow behavior 
  // depending on input parameters
  if(params.event_type == 'activator') {
    activator(event_ch)
    // the output of the activator process is file 
    // to print it: its content should be loaded an covnerted into strings
    activator.out.map(file -> file.text).view()
  } else if (params.event_type == 'processor') {
    processor(event_ch)
    // the output of the processor process is file 
    // to print it: its content should be loaded an covnerted into strings
    processor.out.map(file -> file.text).view()
  } else {
    activator(event_ch)
    processor_input = activator.out.map(file -> file.text)
    processor(processor_input)
    // the output of the processor process is file 
    // to print it: its content should be loaded an covnerted into strings
    processor.out.map(file -> file.text).view()
  }
}
