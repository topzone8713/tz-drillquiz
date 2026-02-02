# Jenkins Kubernetes Pod Template 설정 가이드

## 개요
Jenkins의 Kubernetes Cloud에서 Pod Template을 설정하여 `docker`와 `kubectl` 컨테이너를 포함하는 Pod를 생성하는 방법입니다.

## Jenkins UI에서 Pod Template 등록 방법

### 1. Jenkins 관리 페이지 접속
1. Jenkins 메인 페이지 → **"Manage Jenkins"** 클릭
2. **"Manage Nodes and Clouds"** 클릭
3. **"Configure Clouds"** 클릭
4. **"topzone-k8s"** (또는 Kubernetes Cloud 이름) 클릭

### 2. Pod Template 추가
1. **"Add Pod Template"** 또는 **"Add"** 버튼 클릭
2. **"Kubernetes Pod Template"** 선택

### 3. 기본 설정

#### 3.1 Metadata
- **Name**: `docker-kubectl` (또는 원하는 이름)
- **Namespace**: `jenkins`
- **Labels**: `docker-kubectl` (이 label을 Jenkinsfile에서 사용)
- **Service Account**: `jenkins-admin` (또는 `jenkins`)
- **Node Selector**: `kubernetes.io/os=linux`

#### 3.2 Container 설정

**Container 1: jnlp (Jenkins Agent)**
- **Name**: `jnlp`
- **Docker image**: `jenkins/inbound-agent:3355.v388858a_47b_33-3-jdk21` (또는 최신 버전)
- **Resource requests**:
  - CPU: `512m`
  - Memory: `512Mi`
- **Resource limits**:
  - CPU: `512m`
  - Memory: `512Mi`
- **Environment variables**:
  - `JENKINS_URL`: `http://jenkins.jenkins.svc.cluster.local:8080`
  - `JENKINS_TUNNEL`: `jenkins-agent:50000`

**Container 2: docker**
- **Name**: `docker`
- **Docker image**: `docker:24.0.2-dind` (또는 `docker:26-dind`)
- **Privileged**: ✅ 체크 (필수!)
- **Resource requests**:
  - CPU: `1000m`
  - Memory: `1Gi`
- **Resource limits**:
  - CPU: `2000m`
  - Memory: `2Gi`
- **TTY**: ✅ 체크
- **Command**: `/bin/sh`
- **Arguments**: `-c`
- **Working directory**: `/home/jenkins/agent`
- **Environment variables**:
  - `DOCKER_TLS_CERTDIR`: `` (빈 값)
  - `DOCKER_HOST`: `unix:///var/run/docker.sock` (선택사항)

**Container 3: kubectl**
- **Name**: `kubectl`
- **Docker image**: `doohee323/jenkins-slave` (또는 `bitnami/kubectl:latest`)
- **Privileged**: ✅ 체크 (필요한 경우)
- **Resource requests**:
  - CPU: `512m`
  - Memory: `512Mi`
- **Resource limits**:
  - CPU: `1000m`
  - Memory: `1Gi`
- **TTY**: ✅ 체크
- **Command**: `sleep`
- **Arguments**: `9999999` (doohee323/jenkins-slave 사용 시)
- **Working directory**: `/home/jenkins/agent`

### 4. Volume 설정
- **Workspace Volume**: `emptyDir` 타입
  - Mount path: `/home/jenkins/agent`
  - 모든 컨테이너에서 동일한 경로에 마운트

### 5. YAML 정의 방식 (대안)

Jenkins UI에서 직접 설정하는 대신, **"YAML"** 탭에서 직접 YAML을 입력할 수도 있습니다:

```yaml
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins-admin
  nodeSelector:
    kubernetes.io/os: linux
  containers:
  - name: jnlp
    image: jenkins/inbound-agent:3355.v388858a_47b_33-3-jdk21
    imagePullPolicy: IfNotPresent
    resources:
      requests:
        cpu: 512m
        memory: 512Mi
      limits:
        cpu: 512m
        memory: 512Mi
    env:
    - name: JENKINS_URL
      value: http://jenkins.jenkins.svc.cluster.local:8080
    - name: JENKINS_TUNNEL
      value: jenkins-agent:50000
    volumeMounts:
    - mountPath: /home/jenkins/agent
      name: workspace-volume
    workingDir: /home/jenkins/agent
  - name: docker
    image: docker:24.0.2-dind
    imagePullPolicy: IfNotPresent
    securityContext:
      privileged: true
    resources:
      requests:
        cpu: 1000m
        memory: 1Gi
      limits:
        cpu: 2000m
        memory: 2Gi
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    - name: DOCKER_HOST
      value: unix:///var/run/docker.sock
    tty: true
    command: ["/bin/sh"]
    args: ["-c"]
    volumeMounts:
    - mountPath: /home/jenkins/agent
      name: workspace-volume
    workingDir: /home/jenkins/agent
  - name: kubectl
    image: doohee323/jenkins-slave
    imagePullPolicy: IfNotPresent
    securityContext:
      privileged: true
    command: ["sleep"]
    args: ["9999999"]
    volumeMounts:
    - mountPath: /home/jenkins/agent
      name: workspace-volume
    workingDir: /home/jenkins/agent
  volumes:
  - name: workspace-volume
    emptyDir: {}
```

### 6. Jenkinsfile에서 사용

Pod Template을 등록한 후, Jenkinsfile에서 다음과 같이 사용할 수 있습니다:

**방법 1: Label 사용**
```groovy
pipeline {
    agent {
        kubernetes {
            label 'docker-kubectl'
            defaultContainer 'docker'
        }
    }
    // ...
}
```

**방법 2: Inline YAML 사용 (현재 Jenkinsfile 방식)**
```groovy
pipeline {
    agent {
        kubernetes {
            defaultContainer 'docker'
            yaml """
            # 위의 YAML 정의 사용
            """
        }
    }
    // ...
}
```

## 주의사항

1. **Privileged 모드**: `docker` 컨테이너는 반드시 `privileged: true`로 설정해야 합니다.
2. **Service Account**: Kubernetes 클러스터에서 필요한 권한을 가진 Service Account를 사용해야 합니다.
3. **Image Pull Secrets**: 프라이빗 레지스트리를 사용하는 경우 Image Pull Secret을 설정해야 합니다.
4. **Workspace Volume**: 모든 컨테이너가 동일한 workspace volume을 공유해야 합니다.

## 검증

Pod Template이 제대로 설정되었는지 확인:

1. Jenkins → **"Manage Jenkins"** → **"Manage Nodes and Clouds"**
2. **"Configure Clouds"** → **"topzone-k8s"** 클릭
3. 등록한 Pod Template이 목록에 표시되는지 확인
4. **"Test Connection"** 버튼으로 연결 테스트

## 문제 해결

### "container docker not found" 에러
- Pod Template에 `docker` 컨테이너가 포함되어 있는지 확인
- Label이 Jenkinsfile과 일치하는지 확인
- Pod Template이 활성화되어 있는지 확인

### "container kubectl not found" 에러
- Pod Template에 `kubectl` 컨테이너가 포함되어 있는지 확인
- 컨테이너 이름이 정확한지 확인

### Privileged 컨테이너 실행 실패
- Kubernetes 클러스터에서 privileged 컨테이너 실행이 허용되어 있는지 확인
- Security Policy가 privileged 모드를 차단하지 않는지 확인
