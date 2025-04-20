pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "rostats"
        DOCKER_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/predalau/rostats_aggregator.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                }
            }
        }

        stage('Test SSH') {
           steps {
            sshagent(['your-ssh-key-credential']) {
                sh 'ssh -o StrictHostKeyChecking=no preda@100.70.209.56 "docker ps"'
                }
            }
        }

        stage('Push to Registry') {
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'docker-hub-credentials') {
                        docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push()
                        docker.image("${DOCKER_IMAGE}:latest").push()
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                sshagent(['your-ssh-key-credential']) {
                    sh """
                    ssh -o StrictHostKeyChecking=no preda@http://100.70.209.56 "
                        docker pull ${DOCKER_IMAGE}:${DOCKER_TAG} && \
                        docker stop rostats || true && \
                        docker rm rostats || true && \
                        docker run -d \
                          --name rostats \
                          -p 5000:5000 \
                          -v /app/data:/data \
                          --restart unless-stopped \
                          ${DOCKER_IMAGE}:${DOCKER_TAG}
                    "
                    """
                }
            }
        }
    }
}