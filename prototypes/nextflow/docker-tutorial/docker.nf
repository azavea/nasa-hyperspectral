params.greeting  = 'Hello world!'
greeting_ch = Channel.of(params.greeting)

process foo { 
  container 'ubuntu:latest' 

  input:
  val x from greeting_ch

  output:
  file 'chunk_*' into letters

  """
  printf '$x' | split -b 6 - chunk_
  """
}

process bar {
  container 'ubuntu:latest'

  input:
  file y from letters.flatten()

  output:
  stdout into result

  """
  cat $y | tr '[a-z]' '[A-Z]'
  """
}

result.view{ it.trim() }