pipeline {
  agent any

  environment {
    COMPOSE_PROJECT_NAME = 'charityalmauweb'
    COMPOSE_FILE = 'docker-compose.yml'
  }

  stages {
    stage('Build Docker Images') {
      steps {
        sh '''
          docker-compose build
        '''
      }
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
    success {
      echo '✅ Deployment complete!'
    }
    failure {
      echo '❌ Deployment failed.'
    }
  }
}
