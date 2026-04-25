FROM maven:3.9.9-eclipse-temurin-21 AS builder

WORKDIR /workspace

COPY services/gateway-java/pom.xml /workspace/services/gateway-java/pom.xml
COPY services/gateway-java/src /workspace/services/gateway-java/src

RUN mvn -f /workspace/services/gateway-java/pom.xml -DskipTests package

FROM eclipse-temurin:21-jre

WORKDIR /app

COPY --from=builder /workspace/services/gateway-java/target/gateway-java-0.1.0.jar /app/gateway-java.jar
COPY data /workspace/data

EXPOSE 8080

CMD ["java", "-jar", "/app/gateway-java.jar"]
