# ============================================================
# IAM — Use pre-existing LabRole (Learner Lab restriction)
# ============================================================
# Learner Lab does NOT allow creating IAM roles.
# The LabRole is pre-created with broad permissions and must
# be used for Lambda, API Gateway, and other services.
# ============================================================

data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

# Alias for backward compatibility with resource references
locals {
  lambda_exec_arn = data.aws_iam_role.lab_role.arn
}
