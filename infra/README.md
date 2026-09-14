# Deployment boundary

Recommended first production shape on AWS:

```text
Route 53 / ACM
       |
   CloudFront
    |      |
S3 frontend  ALB -> ECS/Fargate backend
                       |       |
                    RDS PG   private S3 evidence bucket
```

Use one shared, horizontally scalable application fleet—not one deployment per tenant.
Tenant identity is enforced in every repository query and object key. Scale backend tasks on request rate/latency, workers on queue depth, PostgreSQL independently, and CloudFront/S3 automatically.

Start with:

- one RDS PostgreSQL primary with backups and Multi-AZ when production criticality requires it;
- one private S3 bucket with encryption, versioning and lifecycle policies;
- one ECS web service plus one worker service using the same backend image;
- one static frontend build uploaded to an S3 origin behind CloudFront;
- migrations as a one-off release task before backend rollout.

Do not introduce tenant-specific databases, buckets or services until isolation, legal or load evidence proves the need. Tenant-prefixed keys and scoped queries keep the initial design KISS and support thousands of mostly idle tenants cheaply.
