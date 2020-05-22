from aws_cdk import core, aws_lambda, aws_s3, aws_secretsmanager


def get_lambda(scope, name, env_dict={}, layers=[], code_path="./lambda", reserved_concurrent_executions=None):
    return aws_lambda.Function(
        scope=scope,
        id=name,
        function_name=name,
        runtime=aws_lambda.Runtime.PYTHON_3_6,
        handler=f"{name}.handler",
        code=aws_lambda.Code.asset(code_path),
        environment=env_dict,
        layers=layers,
        memory_size=3008,
        timeout=core.Duration.seconds(900),
        reserved_concurrent_executions=reserved_concurrent_executions,
        max_event_age=core.Duration.hours(1)
    )

def get_layer(scope, layer_name, version=1):
    return aws_lambda.LayerVersion.from_layer_version_arn(
        scope=scope,
        id=f"{layer_name}_layer",
        layer_version_arn=f"arn:aws:lambda:eu-west-3:771823009556:layer:{layer_name}:{version}"
    )


def get_secret(scope):
    return aws_secretsmanager.Secret.from_secret_attributes(
        scope=scope,
        id="belean_secret",
        secret_arn=f"arn:aws:secretsmanager:eu-west-3:771823009556:secret:media_analysis_secret-hVRgd7"
    )

def get_project_bucket(scope, bucket_name):    
    return aws_s3.Bucket.from_bucket_name(
        scope=scope,
        id=bucket_name,
        bucket_name=bucket_name
    )