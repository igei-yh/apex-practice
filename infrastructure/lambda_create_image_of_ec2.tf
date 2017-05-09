data "aws_iam_policy_document" "lambda_execution_policy" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "lambda_allow_ec2_action_policy" {
  statement {
    effect = "Allow"

    actions = [
      "logs:*",
    ]

    resources = [
      "arn:aws:logs:*:*:*",
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "ec2:Describe*",
      "ec2:CreateImage",
      "ec2:DeregisterImage",
      "ec2:ModifyImageAttribute",
      "ec2:CreateSnapshot",
      "ec2:DeleteSnapshot",
      "ec2:ModifySnapshotAttribute",
      "ec2:CreateTags",
    ]

    resources = [
      "*",
    ]
  }
}

resource "aws_iam_role_policy" "lambda_allow_ec2_action_policy" {
  name   = "AllowLambdaEC2ActionPolicy"
  role   = "${aws_iam_role.lambda_allow_ec2_action.id}"
  policy = "${data.aws_iam_policy_document.lambda_allow_ec2_action_policy.json}"
}

resource "aws_iam_role" "lambda_allow_ec2_action" {
  name               = "AllowLambdaEC2ActionRole"
  assume_role_policy = "${data.aws_iam_policy_document.lambda_execution_policy.json}"
}

output "AllowLambdaEC2ActionRole" {
  value = "${aws_iam_role.lambda_allow_ec2_action.arn}"
}

variable "apex_function_lambda_auto_backup_name" {}
variable "apex_function_lambda_auto_backup_arn" {}

resource "aws_cloudwatch_event_rule" "lambda_auto_backup" {
  name                = "lambda_auto_backup"
  description         = "auto backup by lambda function"
  schedule_expression = "cron(0 17 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_auto_backup" {
  rule      = "${aws_cloudwatch_event_rule.lambda_auto_backup.name}"
  target_id = "lambda-auto-backup"
  arn       = "${var.apex_function_lambda_auto_backup_arn}"
}

resource "aws_lambda_permission" "lambda_auto_backup" {
  statement_id  = "AllowExecFunctionFromCloudwatch"
  action        = "lambda:InvokeFunction"
  function_name = "${var.apex_function_lambda_auto_backup_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.lambda_auto_backup.arn}"
}

resource "aws_cloudwatch_metric_alarm" "lambda_auto_backup" {
  alarm_name          = "lambda-auto-backup"
  alarm_description   = "auto backup by lambda function"
  namespace           = "lambda"
  metric_name         = "size"
  statistic           = "Average"
  period              = "300"
  unit                = "Bytes"
  evaluation_periods  = "2"
  threshold           = "100000000"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  alarm_actions       = ["arn:aws:sns:ap-northeast-1:888447397082:lambda_auto_backup"]
}
