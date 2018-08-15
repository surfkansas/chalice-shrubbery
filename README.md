# chalice-shrubbery

Chalic Shrubbery is a helper tool for automating AWS Chalice deployments using Cloud Formation.  Its purpose is to provide single-tool support for deploying Chalice microservices using AWS Cloud Formation (as opposed to using Chalice's built-it deploy function).

## Installation

To install Chalice Shrubbery, use pip...

```
pip install chalice-shrubbery
```

Chalice Shrubbery requres both Chalice and the AWS CLI to be installed in the environment where it is used.  These are intentionally omitted from the requirements of this package.

Guidelines for getting started with Chalice are available here:


https://chalice.readthedocs.io

## Configuration

Chalice Shrubbery uses the configuration file created by Chalice.  To configure Chalice Shrubbery, two entries - `shrubbery.s3_bucket` and `shrubbery.stack_name` - should be added to the appropriate stage configuration.

An example of that config is listed here:

```json
{
  "version": "2.0",
  "app_name": "helloworld",
  "api_gateway_stage": "vz",
  "stages": {
    "dev": {
      "shrubbery.s3_bucket": "artifacts-123456789012",
      "shrubbery.stack_name": "hello-world"
    },
    "prod": {
      "shrubbery.s3_bucket": "artifacts-210987654321",
      "shrubbery.stack_name": "hello-world"
    }
  }
}
```

These entries can be at the stage level or the top-level config.

## Config Defaults

If the `shrubbery.s3_bucket` config is not supplied, Chalice Shrubbery will assume a bucket of `chalice-shrubbery-{accountid}`.  You should either configure the bucket, or create the S3 bucket.

If the `shrubbery.stack_name` config is not supplied, Chalice Shrubbery will assume the `app_name` for the stack name.

## Usage

To deploy using Chalice Shrubbery, you call the command line specifying the stage you want to deploy.  Note that Chalice Shrubbery uses the same conventions as Chalice for AWS Authentication.  If a stage is not specified, `dev` will be used as a default.

A sample deployment would be:

```
chalice-shrubbery deploy --stage dev
```

If utilizing a named profile, you can supply that as follows:

```
chalice-shrubbery deploy --stage dev --profile hello-world-dev
```

To delete a deployed stack, use the `delete` action:

```
chalice-shrubbery delete --stage dev
```

Finally, you can describe the stack for a particular stage with the following command:

```
chalice-shrubbery describe --stage dev
```

## Name Origin

The name Chalice Shrubbery came from *Monty Python and the Holy Grail*, as a task given out by the Knights Who Say Ni.

## Version History

* 0.10.108 - 2018-08-15 - (Lancelot)
  * Added post-export transformations to SAM file
  * Added names to Lambda functions
  * Added export names to output
  * Default S3 bucket to chalice-shrubbery-{accountid} if not specified in config
  * Default stack name to dev if not specified in config
  * Config can now be applied at project level

* 0.9.108 - 2018-07-27 - (Sir Robin)
  * Initial release
  * Support for deploy, delete, and describe