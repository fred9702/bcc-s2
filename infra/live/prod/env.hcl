locals {
  environment  = "prod"
  kube_context = "minikube" # would be the prod EKS context, e.g. arn:aws:eks:eu-west-2:<acct>:cluster/bcc-prod
}
