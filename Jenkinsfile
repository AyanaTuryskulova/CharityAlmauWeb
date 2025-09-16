pipeline {
  agent any
  options { skipDefaultCheckout(true) }   // важно
  environment {
    COMPOSE_PROJECT_NAME = 'charityalmauweb'
    COMPOSE_FILE = 'docker-compose.yml'
  }

  stages {
    stage('Checkout') {
      steps {
        cleanWs()           // полная очистка рабочих файлов
        checkout scm
      }
    }

    stage('Prepare .env') {
      steps {
        withCredentials([file(credentialsId: 'charity-env', variable: 'ENV_FILE')]) {
          sh 'cp "$ENV_FILE" .env'
        }
      }
    }

    stage('Build Docker Images') {
      steps { sh 'docker-compose build' }
    }

    stage('Deploy with Docker Compose') {
      steps {
        sh '''
          docker-compose down
          docker-compose up -d
        '''
      }
    }
  }

  post {
    success { echo '✅ Deployment complete!' }
    failure { echo '❌ Deployment failed.' }
  }
}
