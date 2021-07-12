require('ood_core')

script_path = ARGV[0]

clusters = OodCore::Clusters.load_file("/etc/ood/config/clusters.d/")

cluster = clusters["rcs"]
script = OodCore::Job::Script.new(
  content: Pathname.new(script_path).read,
  accounting_id: nil,
  output_path: "job_output",
  error_path: "job_errors"
)
puts cluster.job_adapter.submit(script)
