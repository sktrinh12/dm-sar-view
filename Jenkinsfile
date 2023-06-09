apps = ['sar-view']
pipeline {
    agent { 
        kubernetes{
            inheritFrom 'jenkins-slave'
        }
        
    }
    parameters {
        string(defaultValue: '0.1', description: 'Version number', name: 'VERSION_NUMBER')
		}
    environment{
        AWSID = credentials('AWSID')
        DOCKER_PSW = credentials('DOCKER_PASSWORD')
        DOCKER_CONFIG = "${WORKSPACE}/docker.config"
        NAMESPACE = 'apps'
        APP_NAME = 'sar-view'
        AWS_PAGER = ''
    }

    
    stages {

        stage('docker login') {
            steps {
                    withCredentials([aws(credentialsId: 'awscredentials', region: 'us-west-2')]) {
                    sh '''
                        aws ecr get-login-password \
												--region us-west-2 \
												| docker login --username AWS \
												--password-stdin $AWSID.dkr.ecr.us-west-2.amazonaws.com
                       '''
                }
            }
        }
        
        
        stage('docker build sar-view app') {
            steps{
                sh( label: 'Docker Build $APP_NAME app', script:
                '''
                #!/bin/bash
                set -x
								ls -ltra
                docker build \
                --no-cache --network=host \
                --build-arg REACT_APP_BACKEND_URL=http://geomean.backend.kinnate \
                --build-arg REACT_APP_VERSION=${VERSION_NUMBER} \
                --build-arg REACT_APP_ENVIRONMENT=PROD \
                --memory="2g" --memory-swap="4g" \
                -t $AWSID.dkr.ecr.us-west-2.amazonaws.com/${APP_NAME} \
                -f Dockerfile.prod .
                ''', returnStdout: true
                )
            }
        }
        
        stage('docker push to ecr') {
            steps {
                sh(label: 'ECR docker push $APP_NAME', script:
                '''
                docker push $AWSID.dkr.ecr.us-west-2.amazonaws.com/${APP_NAME}
                ''', returnStdout: true
                )
            }
        }
        
        
        stage('deploy') {
            agent {
                kubernetes {
                  yaml '''
                    apiVersion: v1
                    kind: Pod
                    spec:
                      containers:
                      - name: helm
                        image: alpine/helm:3.11.1
                        command:
                        - cat
                        tty: true
                    '''
                }
            }
            steps{
                container('helm') {
                sh script: '''
                #!/bin/bash
                cd $WORKSPACE
                curl -LO https://storage.googleapis.com/kubernetes-release/release/\$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
                chmod +x ./kubectl
                if ./kubectl get pod -n $NAMESPACE -l app=$APP_NAME | grep -q $APP_NAME; then
                  echo "$APP_NAME pods already exists"
                  ./kubectl rollout restart deploy/${APP_NAME}-deploy -n $NAMESPACE
                else
                  echo "pods $APP_NAME do not exist; deploy using helm"
                  git clone https://github.com/sktrinh12/helm-basic-app-chart.git
                  cd helm-basic-app-chart
                  helm install k8sapp-${APP_NAME} . --set service.namespace=$NAMESPACE \
                  --set service.port=80 --set service.targetPort=80 --set nameOverride=${APP_NAME} \
                  --set fullnameOverride=${APP_NAME} --set namespace=${NAMESPACE} \
                  --set image.repository=${AWSID}.dkr.ecr.us-west-2.amazonaws.com/${APP_NAME} \
                  --set image.tag=latest --set containers.name=react \
                  --set containers.ports.containerPort=80 --set app=${APP_NAME} \
                  --set terminationGracePeriodSeconds=10 --set service.type=ClusterIP \
                  --set ingress.enabled=false --namespace $NAMESPACE
                fi
                '''
                }
            }
        }

        stage ('purge untagged images') {
            steps {
                withCredentials([aws(credentialsId: 'awscredentials', region: 'us-west-2')]) {
                    loop_ecr_purge(apps)
                }
            }
        }
    }
}

def loop_ecr_purge(list) {
    for (int i = 0; i < list.size(); i++) {
        sh """aws ecr list-images \
        --repository-name ${list[i]} \
        --filter 'tagStatus=UNTAGGED' \
        --query 'imageIds[].imageDigest' \
        --output json \
        | jq -r '.[]' \
        | xargs -I{} aws ecr batch-delete-image \
        --repository-name ${list[i]} \
        --image-ids imageDigest={} 
        """
    }
}
