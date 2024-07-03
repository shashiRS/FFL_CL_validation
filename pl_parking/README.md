# PL-Parking Test-Implementations
---

## Table of Contents

- [PL-Parking Test-Implementations](#parking)
  - [Introduction](#introduction)
  - [Pull Request Review Guidelines](#pull-request-review-guidelines)
  - [Implementing New KPIs with Reporting UI](#implementing-new-kpis-with-reporting-ui)
  - [Installation Guide for Reporting UI](#installation-guide-for-reporting-ui)
  - [User Manual for Reporting UI](#user-manual-for-reporting-ui)
  - [Implementing Pre-commit for Development](#implementing-pre-commit-for-development)
  - [Full Testing Pipeline in PARKING (SiCL)](#full-testing-pipeline-in-parking-sicl)
  - [Make Release](#make-release)

## Introduction

Reporistory contains test implementations for PL-Parking

## Pull Request Review Guidelines
Please note:

:warning:
It's important to note that pull requests won't be accepted until the Jenkins build, including code linting, is passed. When a pull request is created, any errors or warnings can be found as annotations in the PR's 'Files Changed' section.

Two Reviews Required: Each pull request must be approved by at least two reviewers.

Code Owner Approval: One of the reviewers must be a designated CODE OWNER for the relevant section.

## Implementing New KPIs with Reporting UI
Implementing a new functional test or Key Performance Indicator (KPI) is straightforward. Utilizing these examples as a foundation can greatly facilitate the development of subsequent tests.

- [Example Test for Implementing New KPIs][example]

## Installation Guide for Reporting UI

Utilizing this comprehensive guide simplifies the tool's installation process, ensuring a quick and seamless setup.

- [Installing Reporting UI][installing]

## User Manual for Reporting UI

A concise and user-friendly manual is provided, ensuring clarity and eliminating any potential questions for seamless future tool utilization.
- [How to use Reporting UI][how-to]

## Implementing Pre-commit for Development

Pre-commit is a powerful tool that helps streamline development workflows by automatically checking code for issues before committing changes. By catching problems early, pre-commit ensures code quality, consistency, and security across the project.
 - [How to use the pre-commit][pre-commit]

## Full Testing Pipeline in PARKING (SiCL)

Discover the comprehensive testing pipeline in PL Parking - SiCL (Simulation Closed Loop)

- [FTP][ftp]

## Make release

A Jenkins job is set up to build and deploy wheels to the Artifactory for install by `pip`.

- Deployment of a wheel to Artifactory is triggered by pushing a git tag.


| :warning:  Important |
|----------------------|
| It is *mandatory to always update* the version number in `pl_parking/__init__.py` for a new release. Otherwise the wheel will be build but not deployed to Artifactory (no overwrite there)  |

Jenkins builds can be checked here: https://ams-adas-tsf-aws-jenkins.eu1.agileci.conti.de/job/pl_parking/view/tags/

Deployed wheel can be checked here: https://eu.artifactory.conti.de/ui/packages?name=adas-pl-parking&type=packages

After deploympent wheels can be installed with `pip install adas-pl-parking`

### Proposal and rough sketch for how to build and deploy a release (wheel) to Artifactory
[This is only a proposal. Concrete process needs to be defined/refined by the project!]

1. Merge all relevant pull requests into `develop` branch
2. Create a release branch from `develop`. For example `release/0.0.3`
3. Update version number in `pl_parking/__init__.py` to release number <- **This step is important**
4. Do additional release specific changes as needed
5. Merge the release branch to `master` branch
6. Tag `master` branch with release number. For example `git tag 0.0.3` <- **This step is important. Tag will trigger deployment to Artifactory**
7. Merge `master` into `develop` branch
8. Push all changes (including tag): `git push && git push --tag`


[example]: https://github-am.geo.conti.de/ADAS/pl_parking/blob/c4dcec545342801096a50176f683a07b1e954cdd/pl_parking/PLP/MF/Example/ft_example_parking_test.py
[installing]: https://confluence.auto.continental.cloud/display/PLP/Installing+Reporting+UI
[how-to]: https://confluence.auto.continental.cloud/display/PLP/How+To+Use+Reporting+UI
[pre-commit]: https://confluence.auto.continental.cloud/display/PLP/Using+pre-commit+in+Development
[ftp]: https://confluence.auto.continental.cloud/pages/viewpage.action?pageId=1395231665
