require('ood_core')

job_id = ARGV[0]

clusters = OodCore::Clusters.load_file("/etc/ood/config/clusters.d/")

cluster = clusters["rcs"]
puts cluster.job_adapter.status(job_id)
