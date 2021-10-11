---
title: "CHAMP is an HPC Access and Metadata Portal"
tags:
  - High Performance Computing
  - Python
  - Metadata
authors:
  - name: Christopher Cave-Ayland
    orcid: 0000-0003-0942-8030
    affiliation: 1
  - name: Michael Bearpark
    orcid: 0000-0002-1117-7536
    affiliation: 2
  - name: Charles Romain
    orcid: 0000-0002-1851-8612
    affiliation: 2
  - name: Henry S. Rzepa^[corresponding author]
    orcid: 0000-0002-8635-8390
    affiliation: 2
affiliations:
  - name: Imperial College London, Research Computing Service
    index: 1
  - name: Imperial College London, Department of Chemistry
    index: 2
date: 08 October 2021
bibliography: refs.bib
---

# Summary

CHAMP (CHAMP is an HPC Access and Metadata Portal) provides an easy to use
workflow for FAIR data generation and publication using high performance
computing (HPC) resources. It provides a web based interface allowing submission
of HPC workloads and subsequent one-click publication of the results to data
repositories such as Zenodo. Depositions support rich metadata to repositories
that include a full implemention of the Subject property of the DataCite
metadata schema [@datacite].

Users submit jobs simply by choosing from pre-configured software and computing
resource specifications:

![The form for the initial step in job creation](docs/images/resources.png)

The user is then asked to upload the required input files for their chosen
software and may optionally provide a job description:

![The form for the file upload step in job creation](docs/images/job_files.png)

The status of jobs is available via a dedicated view. Publication to data
repositories is also possible once the job has completed, with the reserved
persistent identifier (a DOI) shown associated with the job.

![Summary table of jobs run using the portal](docs/images/job_list.png)

CHAMP makes use of the Open OnDemand [@Hudak2018] framework. This allows CHAMP
to be portable across different HPC systems and to integrate flexibly with
institutional infrastructure (e.g. authentication mechanisms).

CHAMP represents over 15 years of experimentation in HPC portal design
[@Harvey2014]. The recent 2.0 release is a ground up rewrite to facilitate its
publication as an open-source package, to modernise the code base and to address
isues of portability and sustainability.

# Statement of Need

Access to HPC resources has traditionally been available almost exclusively via
command line interfaces which can present a barrier to entry for new and
occasional users. The web interface provided by CHAMP is simple and intuitive
providing an ideal entry point for non-experts.

Open OnDemand, the framework used by CHAMP, also provides a web based interface
for HPC job submission. CHAMP differs by providing a higher level of abstraction
that completely removes the need to deal with shell scripts or scheduler
directives. This trade-off makes CHAMP much easier to use but introduces the
restriction that only pre-configured software and resource configurations are
supported.

The ability to publish job outputs to data repositories greatly simplifies the
process of producing metadata-enabled FAIR datasets. The relevant files to
upload and various rich metadata items are collected using workflows based on
the selected software.

# Implementation and Features

CHAMP is written as a Passenger App within the Open OnDemand (OOD) framework. It
must therefore be deployed within a local OOD instance. Use of OOD provides
numerous advantages such as portability, a strong security model and an active
community of users. This allows the CHAMP code base to be quite minimal with
mechanisms for authenticaton and system scheduler interaction provided by the
parent framework. The per-user NGINX architecture of OOD ensures all relevant
computational processes are run under individual user UIDs.

CHAMP is written in Python (>=3.7) using Django [@django] and supports extensive
customisation via its main YAML configuration file. Administrators may configure
the relevant software packages and resource configurations for their local
system. There are no restrictions on the software or resource types that may be
configured. Arbitrary workflows may be used to run software and to generate
metadata. This allows flexibility to e.g. use a job restart file if uploaded by
a user or vary metadata for publication depending on job inputs.

The workflow that CHAMP imposes for HPC usage also provides inherent
reproducibility. Individual jobs are structured within separate directories with
relevant input files and scripts present. Jobs are recorded with metadata such
as resources used and a free text description and are organised into
projects. Job history can be filtered and searched according to this metadata
allowing the portal to act as a simple electronic lab notebook.

An integration with Zenodo is included in the code base. Additional data
repositories that support interaction via API and OAuth2 authentication may be
configured via a plugin mechanism. This allows the development of custom
integrations with institutional data repositories where desired, in the case of
Imperial College with an existing repository service [@Harvey2017].

# Acknowledgments

We acknowledge the extensive contributions of Dr Matthew Harvey for work on
version 1 of this software.

# References
