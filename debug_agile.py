import re

resume_text = """
Sai Vishruth V
United States | +1(469) 629-6350 | valandassaivishruth@gmail.com

PROFESSIONAL SUMMARY
Lead Full-Stack Engineer driving scalable, cloud native solutions for healthcare and retail. Senior level professional with deep expertise
in Java/Kotlin microservices, AWS serverless architectures, and CI/CD automation. Delivered an enterprise AI augmented RAG platform
that reduced data retrieval time by 30% and architected a HIPAA Compliant healthcare portal serving millions of users. Seeking to apply
this blend of full stack and cloud leadership to accelerate innovative product delivery.

PROFESSIONAL EXPERIENCES
HCA HealthCare Aug 2024 - Present
Senior Software engineer
• Architected and delivered enterprise healthcare and HR platforms using Java 17+, Kotlin, Spring Boot, React/Angular, and
REST/GraphQL APIs, enabling HIPAA-compliant data flows, secure authentication, and seamless integration with Oracle Fusion,
MuleSoft, and hospital systems on Azure.
• Designed and implemented cloud-native, event-driven microservices with Spring Cloud, Kafka, Redis, PostgreSQL, Docker, and
Kubernetes (AKS/EKS), migrating monoliths into scalable distributed systems and automating infrastructure using Terraform, Helm,
and Ansible.
• Built Java Spring Boot microservices from scratch including API contracts, domain models, security layers, Dockerization,
Kubernetes manifests, and CI/CD pipelines, ensuring high availability, performance, and secure deployment practices.
• Developed responsive and accessible UI applications using React, TypeScript, Tailwind, Material UI, and Storybook, integrating
SSO and IAM providers such as Azure AD, Okta, and Auth0 using OAuth2, OpenID Connect, SAML, and JWT.
• Led requirements analysis and solution design sessions with product owners, clinicians, and HR stakeholders, translating complex
healthcare workflows into scalable technical designs while balancing compliance, performance, and usability.
• Implemented BDD and TDD practices using Cucumber, JUnit, Mockito, Selenium, and TestNG, and applied DevSecOps tooling
including SonarQube, Checkmarx, Fortify, Snyk, and Trivy to improve code quality, security posture, and release confidence.
• Acted as the technical owner for high-impact services, resolving production incidents, performing root cause analysis, optimizing
SQL and data pipelines with Kafka, Snowflake, Cosmos DB, and Azure Data Factory, and improving system reliability and MTTR.
• Iterated on product features based on customer feedback, production metrics, and stakeholder input to continuously improve
usability, performance, and reliability.
• Mentored junior and mid-level engineers through code reviews, design discussions, and best-practice guidance, improving code
quality, delivery confidence, and team productivity.
• Communicated project status, risks, and trade-offs clearly to product owners, stakeholders, and cross-functional teams, enabling
informed decision-making.

Capital One May 2021 - Jul 2023
Senior Software engineer
• Engineered low-latency, distributed Java microservices using Spring Boot, gRPC, Redis, Elasticsearch, GraphQL, and Apache Qpid,
achieving sub-10ms performance for high-volume financial data processing.
• Created normalized and analytical data models to support transactional systems and downstream reporting pipelines.
• Developed high-performance backend services using Java and Spring Boot, leveraging stored procedures and optimized queries for
mission-critical workloads.
• Designed secure communication patterns between trusted control services and isolated execution environments using gRPC-based
IPC with strict policy enforcement and runtime constraints.
• Implemented container isolation and runtime security controls using Kubernetes security contexts, Linux namespaces, cgroups,
syscall filtering (seccomp), and network segmentation policies to enforce strict isolation boundaries for sensitive workloads.
• Integrated application monitoring and performance diagnostics using Dynatrace alongside Prometheus, Grafana, ELK, and Splunk
to analyze JVM performance, API latency, memory leaks, and production bottlenecks.
• Designed and optimized Kafka-based streaming pipelines and JMS/AMQP messaging using Apache Qpid, reducing real-time response
time by 40% and improving protocol reliability under heavy load with asynchronous I/O (WebFlux, CompletableFuture) and multi-
threaded parallelism.
• Built faultolerant, highly available cloud architectures with active deployments, circuit breaker patterns, blue green/canary rollouts,
auto scaling, and zero downtime CI/CD pipelines in jenkins/GitHub Actions across AWS ECS, Lambda, API Gateway, and
DynamoDB, achieving the 99.9999% uptime target.
• Implemented end-to-end observability and reliability engineering with OpenTelemetry, Prometheus, Grafana, ELK, and chaos testing
to meet SLA/SLO targets; collaborated with SRE/DevOps teams on resilience validation, proactive alerting, and error budget strategies.
• Developed secure, PCI-DSS and SOX-compliant microservices integrating core banking implementing identity federation using
OAuth2, SAML, JWT, AWS Cognito, and IAM for SSO and secure transactions.
• Modernized backend APIs with Node.js, GraphQL, and schema-driven architecture; designed schemas, resolvers, and API contracts
"""

resume_text_lower = resume_text.lower()

# EXACT LOGIC FROM utils.py
strict_patterns = [r'\bagile\b', r'\bscrum\b', r'\bkanban\b', r'\bextreme programming\b', r'\bscrumban\b']

print("--- DEBUGGING REGEX MATCHES ---")
found_any = False
for p in strict_patterns:
    matches = list(re.finditer(p, resume_text_lower))
    if matches:
        found_any = True
        print(f"Pattern '{p}' MATCHED:")
        for m in matches:
            print(f"  - Quote: '{m.group(0)}' at index {m.start()}")
            # Show context
            start = max(0, m.start() - 20)
            end = min(len(resume_text), m.end() + 20)
            print(f"  - Context: ...{resume_text[start:end]}...")
    else:
        print(f"Pattern '{p}' did NOT match.")

if not found_any:
    print("\nRESULT: No Agile keywords found. The Logic SHOULD have downgraded.")
else:
    print("\nRESULT: Agile keywords FOUND. The Logic Correctly kept it Full.")
