pipeline {
    agent any

    environment {
        REMOTE_DIR = "${params.REMOTE_DIR ?: 'WORKFILES'}"
        REMOTE_SERVER = "${params.REMOTE_SERVER ?: 'ii.happydebt.kz'}"
        GIT_CREDENTIALS = "${params.GIT_CREDENTIALS ?: 'ssh-key'}"
        GIT_DEPLOY_BRANCH = "${params.GIT_DEPLOY_BRANCH ?: '*/main'}"
        DOCKER_DEPLOYMENT_TARGET = "${params.DOCKER_DEPLOYMENT_TARGET ?: 'vllm-keepalive'}"

        PROJECT_NAME = "vllm-keepalive"
        PROJECT_DIR = "${env.REMOTE_DIR}/${PROJECT_NAME}"
        TARBALL_NAME = "${PROJECT_NAME}.tar.gz"
        GIT_REPOSITORY_URL = "git@github.com:ServicePCT/${PROJECT_NAME}.git"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: env.GIT_DEPLOY_BRANCH]],
                    userRemoteConfigs: [[
                        url: env.GIT_REPOSITORY_URL,
                        credentialsId: env.GIT_CREDENTIALS
                    ]],
                    extensions: [
                        [
                            $class: 'SubmoduleOption',
                            disableSubmodules: false,
                            recursiveSubmodules: true,
                            parentCredentials: true
                        ]
                    ]
                ])
                
                sh '''
                    echo "=== Verifying checkout ==="
                    git log -1 --oneline
                '''
            }
        }
        
        stage('Prepare Remote Directory') {
            steps {
                sshPublisher(
                    publishers: [
                        sshPublisherDesc(
                            configName: env.REMOTE_SERVER,
                            transfers: [
                                sshTransfer(
                                    execCommand: '''
                                        #!/bin/bash
                                        set -ex
                                        
                                        echo "=== Preparing remote directory ==="
                                        
                                        rm -rf ''' + env.PROJECT_DIR + '''
                                        mkdir -p ''' + env.PROJECT_DIR + '''
                                        
                                        echo "=== Directory prepared ==="
                                        ls -la ''' + env.REMOTE_DIR + '''
                                    '''
                                )
                            ],
                            verbose: true
                        )
                    ]
                )
            }
        }
        
        stage('Copy Files to Remote') {
            steps {
                script {
                    sh '''
                        echo "=== Creating tarball ==="
                        
                        tar --exclude='.git' \
                            --exclude='.gitignore' \
                            --exclude=''' + env.TARBALL_NAME + ''' \
                            -czf ''' + env.TARBALL_NAME + ''' . || [ -f ''' + env.TARBALL_NAME + ''' ]
                        
                        if [ ! -f ''' + env.TARBALL_NAME + ''' ]; then
                            echo "ERROR: Tarball was not created!"
                            exit 1
                        fi
                        
                        echo "=== Tarball created ==="
                        ls -lh ''' + env.TARBALL_NAME + '''
                    '''
                }
                
                sshPublisher(
                    publishers: [
                        sshPublisherDesc(
                            configName: env.REMOTE_SERVER,
                            transfers: [
                                sshTransfer(
                                    sourceFiles: env.TARBALL_NAME,
                                    removePrefix: '',
                                    remoteDirectory: env.REMOTE_DIR
                                ),
                                sshTransfer(
                                    execCommand: '''
                                        #!/bin/bash
                                        set -ex
                                        
                                        cd ''' + env.PROJECT_DIR + '''
                                        
                                        echo "=== Extracting tarball ==="
                                        tar -xzf ../''' + env.TARBALL_NAME + '''
                                        rm ../''' + env.TARBALL_NAME + '''
                                        
                                        echo "=== Files extracted ==="
                                        ls -la
                                        
                                        echo "=== File count ==="
                                        find . -type f | wc -l
                                    '''
                                )
                            ],
                            verbose: true
                        )
                    ]
                )
            }
        }
        
        stage('Configure Environment') {
            steps {
                sshPublisher(
                    publishers: [
                        sshPublisherDesc(
                            configName: env.REMOTE_SERVER,
                            transfers: [
                                sshTransfer(
                                    execCommand: '''
                                        #!/bin/bash
                                        set -ex
                                        
                                        echo "=== Configuring environment ==="
                                        cd ''' + env.PROJECT_DIR + '''
                                        
                                        # Get host IP (first address from hostname -I)
                                        HOST_IP=$(hostname -I | awk '{print $1}')
                                        echo "Detected host IP: ${HOST_IP}"
                                        
                                        # Copy env.example to .env and replace VLLM_HOST
                                        cp env.example .env
                                        sed -i "s/^VLLM_HOST=.*/VLLM_HOST=${HOST_IP}/" .env
                                        
                                        echo "=== Environment configured ==="
                                        cat .env
                                    '''
                                )
                            ],
                            verbose: true
                        )
                    ]
                )
            }
        }
        
        stage('Deploy') {
            steps {
                sshPublisher(
                    publishers: [
                        sshPublisherDesc(
                            configName: env.REMOTE_SERVER,
                            transfers: [
                                sshTransfer(
                                    execCommand: '''
                                        #!/bin/bash
                                        set -ex
                                        
                                        echo "=== Deploying application ==="
                                        cd ''' + env.PROJECT_DIR + '''
                                        
                                        docker compose down || true
                                        docker compose up -d ''' + env.DOCKER_DEPLOYMENT_TARGET + ''' --build
                                        
                                        echo "=== Checking container status ==="
                                        docker compose ps -a
                                        
                                        echo "=== Deployment complete ==="
                                    '''
                                )
                            ],
                            verbose: true
                        )
                    ]
                )
            }
        }
    }
    
    post {
        success {
            echo "Deployment successful to ${PROJECT_DIR}!"
        }
        
        failure {
            echo 'Deployment failed!'
        }

        always {
            sh 'rm -f *.tar.gz || true'
        }
    }
}



