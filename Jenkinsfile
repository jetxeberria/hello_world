node('docker') {
    checkout scm
    stage('Build') {
        docker.image('jetxeberria/astrodocker:latest').inside {
            sh 'python --version'
        }
    }
}