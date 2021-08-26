require('ood_core')

job_id = ARGV[0]

clusters = OodCore::Clusters.load_file("/etc/ood/config/clusters.d/")

cluster = clusters[ARGV[1]]
puts cluster.job_adapter.delete(job_id)
