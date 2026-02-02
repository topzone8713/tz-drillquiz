# Jenkins Agent 연결 문제 해결 가이드

## 문제 증상

Jenkins Agent Pod가 Jenkins Master에 연결하지 못하고 다음 에러가 발생:

```
java.io.IOException: Failed to connect to http://jenkins.jenkins.svc.cluster.local/tcpSlaveAgentListener/: Connection refused
```

## 확인된 설정

### 1. Jenkins Master 설정 (values.yaml)

```yaml
controller:
  # Agent listener 설정
  agentListenerEnabled: true
  agentListenerPort: 50000
  
  # 비활성화된 Agent 프로토콜 (주의!)
  disabledAgentProtocols:
    - JNLP-connect
    - JNLP2-connect
```

### 2. Kubernetes Plugin 설정

Jenkins Master의 `/var/jenkins_home/config.xml`에서 확인된 설정:
- `jenkinsUrl`: `http://jenkins.jenkins.svc.cluster.local`
- `jenkinsTunnel`: `jenkins-agent:50000`
- `slaveAgentPort`: `50000`

### 3. Agent Pod 환경 변수

```bash
JENKINS_URL=http://jenkins.jenkins.svc.cluster.local/
JENKINS_TUNNEL=jenkins-agent:50000
```

## 문제 원인 분석

1. **네트워크 연결은 정상**: Agent Pod에서 curl로 테스트하면 200 응답
2. **포트 연결도 정상**: `nc -zv jenkins.jenkins.svc.cluster.local 8080` 성공
3. **JNLP 연결만 실패**: JNLP Agent가 tcpSlaveAgentListener에 연결할 때 Connection refused

## 필요한 설정 확인 사항

### 1. Jenkins Master의 TCP Slave Agent Listener 활성화 확인

Jenkins 웹 UI에서 확인:
1. `http://jenkins.jenkins.svc.cluster.local:8080/configureSecurity/` 접근
2. "TCP port for inbound agents" 섹션 확인
3. 포트가 50000으로 설정되어 있고 활성화되어 있는지 확인

또는 Jenkins Master Pod에서:
```bash
kubectl exec -n jenkins jenkins-0 -- curl -s http://localhost:8080/tcpSlaveAgentListener/
```

### 2. JNLP 프로토콜 설정 확인

현재 `values.yaml`에서 `JNLP-connect`와 `JNLP2-connect`가 비활성화되어 있지만, 
Kubernetes Plugin은 일반적으로 `JNLP4-connect`를 사용하므로 문제가 아닐 수 있습니다.

하지만 확인이 필요합니다:
- Jenkins 웹 UI: `Manage Jenkins` → `Configure Global Security` → `Agent protocols`
- `JNLP4-connect`가 활성화되어 있어야 함

### 3. Jenkins URL 설정 확인

Kubernetes Plugin 설정에서:
- **Jenkins URL**: `http://jenkins.jenkins.svc.cluster.local` (또는 `http://jenkins.jenkins.svc.cluster.local/`)
- **Jenkins tunnel**: `jenkins-agent:50000`

### 4. 서비스 및 엔드포인트 확인

```bash
# Jenkins 서비스 확인
kubectl get svc jenkins -n jenkins

# Jenkins Agent 서비스 확인
kubectl get svc jenkins-agent -n jenkins

# 엔드포인트 확인
kubectl get endpoints jenkins -n jenkins
kubectl get endpoints jenkins-agent -n jenkins
```

## 해결 방법

### 방법 1: Jenkins Master 재시작 (가장 간단)

Jenkins Master가 완전히 시작되기 전에 Agent가 연결을 시도했을 수 있습니다.

```bash
kubectl rollout restart statefulset jenkins -n jenkins
```

### 방법 2: Jenkins 웹 UI에서 설정 확인 및 수정

1. Jenkins 웹 UI 접근
2. `Manage Jenkins` → `Configure Global Security`
3. "TCP port for inbound agents" 섹션에서:
   - 포트가 50000으로 설정되어 있는지 확인
   - "Fixed" 또는 "Random" 선택 확인
4. "Agent protocols" 섹션에서:
   - `JNLP4-connect`가 활성화되어 있는지 확인

### 방법 3: Kubernetes Plugin 설정 확인

1. Jenkins 웹 UI: `Manage Jenkins` → `Configure Clouds`
2. Kubernetes 클라우드 설정 확인:
   - **Jenkins URL**: `http://jenkins.jenkins.svc.cluster.local`
   - **Jenkins tunnel**: `jenkins-agent:50000`
   - "Test Connection" 버튼으로 연결 테스트

### 방법 4: values.yaml 수정 (필요시)

만약 JNLP 프로토콜 문제라면:

```yaml
controller:
  disabledAgentProtocols: []  # 모든 프로토콜 활성화
  # 또는
  disabledAgentProtocols:
    - JNLP-connect
    - JNLP2-connect
    # JNLP4-connect는 활성화 유지
```

### 방법 5: Agent Pod 재생성

문제가 있는 Agent Pod를 삭제하면 Jenkins가 자동으로 새 Pod를 생성합니다:

```bash
kubectl delete pod <agent-pod-name> -n jenkins
```

## 현재 상태 확인 명령어

```bash
# Jenkins Master 상태
kubectl get pod jenkins-0 -n jenkins

# Agent Pod 상태
kubectl get pod -n jenkins | grep docker

# Jenkins Master 로그
kubectl logs jenkins-0 -n jenkins --tail=50

# Agent Pod 로그
kubectl logs <agent-pod-name> -n jenkins -c jnlp --tail=50

# 네트워크 연결 테스트
kubectl exec -n jenkins <agent-pod-name> -c jnlp -- curl -s -o /dev/null -w "%{http_code}" http://jenkins.jenkins.svc.cluster.local:8080/tcpSlaveAgentListener/
```

## 발견된 현상

**중요한 발견**:
- Agent Pod에서 `curl`로 `tcpSlaveAgentListener` 접근: ✅ **성공** (200 OK)
- Jenkins Master에서 `curl`로 테스트: ✅ **성공** (200 OK)
- JNLP Agent의 Java HTTP 연결 (호스트명 사용): ❌ **실패** (Connection refused)
- **JNLP Agent의 Java HTTP 연결 (IP 직접 사용)**: ✅ **성공** (`Remoting server accepts the following protocols: [JNLP4-connect, Ping]`)

**DNS 해석 테스트 결과**:
- `getent hosts jenkins.jenkins.svc.cluster.local`: ✅ **성공** (10.233.9.36)
- `curl`로 호스트명 접근: ✅ **성공**
- Java agent로 호스트명 접근: ❌ **실패**
- Java agent로 IP 직접 접근: ✅ **성공**

**현재 설정**:
- `jenkinsUrl`: `http://jenkins.jenkins.svc.cluster.local/` (trailing slash 포함)
- `jenkinsTunnel`: `jenkins-agent:50000` (정상)
- `directConnection`: `false` (비활성화)
- `websocket`: `false` (비활성화)

**분석**:
- **DNS 해석 자체는 정상**: `getent hosts`와 `curl` 모두 성공
- **Java HTTP 클라이언트의 DNS/연결 문제**: Java agent가 호스트명으로 연결할 때만 실패
- **IP로 직접 연결하면 성공**: Java agent가 IP 주소를 직접 사용하면 정상 작동
- **"Could not locate server among [http://jenkins.jenkins.svc.cluster.local/]"**: Java의 HTTP 클라이언트가 DNS 해석 또는 연결 과정에서 문제 발생

## 예상 원인

가장 가능성 높은 원인:
1. **Java HTTP 클라이언트의 연결 타이밍 문제**: Agent가 연결을 시도하는 순간 Jenkins Master가 일시적으로 응답하지 않음
2. **Jenkins Master의 HTTP 서버가 특정 User-Agent나 헤더를 거부할 수 있음**
3. **Java의 네트워크 설정 문제** (IPv6 우선 시도 등)
4. **Jenkins Master의 tcpSlaveAgentListener가 제대로 시작되지 않음** (하지만 curl은 성공)

## 해결 방법

### 방법 1: Jenkins URL을 IP 주소로 변경 (가장 확실한 해결책) ⭐

Java HTTP 클라이언트의 DNS 문제를 우회하기 위해 Jenkins URL을 IP 주소로 직접 설정:

1. Jenkins Master의 IP 주소 확인:
   ```bash
   kubectl get svc jenkins -n jenkins -o jsonpath='{.spec.clusterIP}'
   # 예: 10.233.9.36
   ```

2. Jenkins 웹 UI에서 설정 변경:
   - `Manage Jenkins` → `Configure Clouds` → Kubernetes 설정
   - **Jenkins URL**: `http://10.233.9.36:8080` (IP 주소 직접 사용)
   - 또는 Kubernetes Plugin의 Pod Template에서 `JENKINS_URL` 환경 변수 설정

3. 또는 values.yaml에서 설정:
   ```yaml
   agent:
     envVars:
       - name: JENKINS_URL
         value: "http://10.233.9.36:8080"  # Jenkins Service의 ClusterIP
   ```

**테스트 결과**: IP 주소를 사용하면 Java agent가 정상적으로 연결됨 (`Remoting server accepts the following protocols: [JNLP4-connect, Ping]`)

### 방법 2: Java DNS 캐싱 비활성화 및 시스템 속성 설정

Agent Pod에 Java 시스템 속성 추가 (values.yaml):
```yaml
agent:
  envVars:
    - name: JAVA_OPTS
      value: "-Djava.net.preferIPv4Stack=true -Djava.net.useSystemProxies=false -Dsun.net.useExclusiveBind=false -Djava.net.useSystemProxies=false -Dnetworkaddress.cache.ttl=0 -Dnetworkaddress.cache.negative.ttl=0"
```

- `-Dnetworkaddress.cache.ttl=0`: DNS 캐시 TTL을 0으로 설정 (캐싱 비활성화)
- `-Dnetworkaddress.cache.negative.ttl=0`: 실패한 DNS 조회 캐시 비활성화

### 방법 3: Jenkins URL에 포트 번호 명시

Jenkins URL에 포트 번호를 명시적으로 포함:
- `http://jenkins.jenkins.svc.cluster.local:8080` (포트 명시)
- trailing slash 제거: `/` 제거

### 방법 4: Direct Connection 활성화

Kubernetes Plugin 설정에서:
- **Direct Connection**: 체크박스 활성화
- 이것은 Agent가 직접 Jenkins Master에 연결하도록 합니다

### 방법 5: WebSocket 활성화

Kubernetes Plugin 설정에서:
- **WebSocket**: 체크박스 활성화
- WebSocket을 통한 연결은 더 안정적일 수 있습니다

## CoreDNS 및 DNS 문제 분석

### CoreDNS 상태 확인

**CoreDNS Pod 상태**:
- CoreDNS Pod: ✅ 정상 실행 중 (2개 replica)
- CoreDNS Service: ✅ 정상 (`10.233.0.3:53`)
- CoreDNS Endpoints: ✅ 정상 (2개 endpoint)

**CoreDNS 설정**:
```yaml
.:53 {
    errors {
    }
    health {
        lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
      pods insecure
      fallthrough in-addr.arpa ip6.arpa
    }
    prometheus :9153
    forward . /etc/resolv.conf {
      prefer_udp
      max_concurrent 1000
    }
    cache 30
    loop
    reload
    loadbalance
}
```

**CoreDNS 로그**:
- 외부 DNS 쿼리 타임아웃: `[ERROR] plugin/errors: 2 ... HINFO: read udp ...: i/o timeout`
- 이는 외부 DNS 서버(10.0.2.3:53)로의 쿼리 타임아웃으로, 클러스터 내부 DNS 해석과는 무관

### DNS 해석 테스트 결과

**정상 작동**:
- `getent hosts jenkins.jenkins.svc.cluster.local`: ✅ 성공 (10.233.9.36)
- `curl http://jenkins.jenkins.svc.cluster.local:8080/...`: ✅ 성공
- `/etc/resolv.conf`: 정상 설정 (nameserver: 169.254.25.10, search domains 포함)

**실패**:
- Java HTTP 클라이언트 (호스트명 사용): ❌ Connection refused
- Java HTTP 클라이언트 (IP 직접 사용): ✅ 성공

### 문제 원인 분석

**CoreDNS 자체는 문제 없음**:
- CoreDNS는 정상 작동 중
- 클러스터 내부 DNS 해석은 정상 (`getent hosts`, `curl` 모두 성공)

**Java HTTP 클라이언트의 DNS 해석 문제**:
1. **DNS 해석 타이밍**: Java의 `InetAddress.getByName()`이 DNS 해석 중 타임아웃 발생 가능
2. **DNS 캐싱**: Java는 DNS 결과를 캐싱하는데, 실패한 결과도 캐싱할 수 있음
3. **ndots 설정**: `/etc/resolv.conf`의 `ndots:5` 설정으로 인해 검색 도메인 순회 시 오버헤드 발생
4. **동기식 DNS 해석**: Java의 표준 DNS 해석은 동기식이며, 타임아웃 설정이 엄격할 수 있음

**"Could not locate server among [http://jenkins.jenkins.svc.cluster.local/]"**:
- 이 메시지는 Java HTTP 클라이언트가 DNS 해석 또는 연결 과정에서 실패했음을 의미
- `getent hosts`와 `curl`은 성공하지만 Java만 실패하는 것은 Java의 DNS 해석 메커니즘 문제

### 해결 방법 (우선순위 순)

#### 1. Jenkins URL을 IP 주소로 변경 (가장 확실) ⭐

**이미 적용됨**:
```yaml
agent:
  jenkinsUrl: "http://10.233.9.36:8080"  # IP 주소 직접 사용
```

**장점**:
- DNS 해석 과정을 완전히 우회
- 가장 확실하고 빠른 해결책
- Java HTTP 클라이언트의 DNS 문제와 무관하게 작동

**단점**:
- IP 주소가 변경되면 수동으로 업데이트 필요
- 하지만 Service의 ClusterIP는 일반적으로 변경되지 않음

#### 2. Java DNS 캐싱 비활성화 및 타임아웃 조정

values.yaml에 추가:
```yaml
agent:
  envVars:
    - name: JAVA_OPTS
      value: "-Djava.net.preferIPv4Stack=true -Djava.net.useSystemProxies=false -Dnetworkaddress.cache.ttl=0 -Dnetworkaddress.cache.negative.ttl=0 -Dsun.net.useExclusiveBind=false"
```

**설명**:
- `-Dnetworkaddress.cache.ttl=0`: DNS 캐시 TTL을 0으로 설정 (캐싱 비활성화)
- `-Dnetworkaddress.cache.negative.ttl=0`: 실패한 DNS 조회 캐시 비활성화
- `-Dsun.net.useExclusiveBind=false`: 소켓 바인딩 문제 방지

#### 3. CoreDNS 설정 최적화 (선택사항)

CoreDNS ConfigMap 수정:
```yaml
forward . /etc/resolv.conf {
  prefer_udp
  max_concurrent 1000
  health_check 5s
}
cache 30 {
  success 9984 30
  denial 9984 5
}
```

**설명**:
- `health_check`: 업스트림 DNS 서버 헬스 체크
- `cache` 최적화: 성공/실패 캐시 TTL 조정

#### 4. NodeLocalDNS 추가 (고급, 선택사항)

클러스터에 NodeLocalDNS를 추가하여 DNS 해석 지연 감소:
- 각 노드에 로컬 DNS 캐시 추가
- CoreDNS로의 트래픽 감소
- DNS 해석 지연 감소

### 결론

**CoreDNS는 정상 작동 중**이며, 문제는 **Java HTTP 클라이언트의 DNS 해석 메커니즘**에 있습니다.

**권장 해결책**:
1. ✅ **Jenkins URL을 IP 주소로 변경** (이미 적용됨, 가장 확실)
2. Java DNS 캐싱 비활성화 (추가 보완)
3. CoreDNS 최적화 (선택사항)

IP 주소를 사용하는 것이 가장 확실하고 간단한 해결책입니다.

## 추가 발견 사항: JDK Installations

**JDK Installations 설정 확인**:
- Jenkins config.xml: `<jdks/>` (빈 태그 - JDK installations가 설정되지 않음)
- Agent Pod 내부: Java 17 설치됨 (`/opt/java/openjdk`, OpenJDK 17.0.14)
- Jenkinsfile: `tool` 명령어로 JDK를 지정하는 부분 없음

**영향 분석**:
- **Agent 연결 문제와는 무관**: JDK installations 설정은 빌드 도구 관리용이며, Agent 연결 자체와는 관련 없음
- **현재 상태**: Agent Pod에 Java가 이미 설치되어 있고, Jenkinsfile에서 `tool` 명령어를 사용하지 않으므로 문제 없음
- **필요한 경우**: Pipeline에서 특정 JDK 버전을 명시적으로 지정하려면 JDK installations 설정 필요

**JDK installations 설정 방법** (필요한 경우):
1. Jenkins 웹 UI: `Manage Jenkins` → `Tools` → `JDK installations`
2. JCasC로 설정 (values.yaml의 `JCasC.configScripts`):
   ```yaml
   controller:
     JCasC:
       configScripts:
         jdk-config: |
           jenkins:
             tool:
               jdk:
                 installations:
                 - name: "JDK-17"
                   home: "/opt/java/openjdk"
   ```

## 권장 조치 (우선순위 순)

### 1. Jenkins URL을 IP 주소로 변경 (가장 확실한 해결책) ⭐

**values.yaml 수정**:
```yaml
agent:
  jenkinsUrl: "http://10.233.9.36:8080"  # Jenkins Service의 ClusterIP
```

**적용 방법**:
```bash
# Jenkins Service의 ClusterIP 확인
kubectl get svc jenkins -n jenkins -o jsonpath='{.spec.clusterIP}'

# values.yaml 수정 후 Helm 업그레이드
cd provisioning/jenkins/helm
helm upgrade jenkins jenkins/jenkins \
  --namespace jenkins \
  --version 5.8.116 \
  -f values.yaml
```

**또는 Jenkins 웹 UI에서**:
- `Manage Jenkins` → `Configure Clouds` → Kubernetes 설정
- **Jenkins URL**: `http://10.233.9.36:8080` (IP 주소 직접 사용)

### 2. Direct Connection 활성화

Jenkins 웹 UI에서:
- `Manage Jenkins` → `Configure Clouds` → Kubernetes 설정
- **Direct Connection**: 체크박스 활성화

또는 values.yaml:
```yaml
agent:
  directConnection: true
```

### 3. Java DNS 캐싱 비활성화

values.yaml에 추가:
```yaml
agent:
  envVars:
    - name: JAVA_OPTS
      value: "-Djava.net.preferIPv4Stack=true -Djava.net.useSystemProxies=false -Dnetworkaddress.cache.ttl=0 -Dnetworkaddress.cache.negative.ttl=0"
```

### 4. Jenkins Master 재시작

```bash
kubectl rollout restart statefulset jenkins -n jenkins
```

### 5. 문제가 지속되면 Agent Pod 재생성

```bash
kubectl delete pod <agent-pod-name> -n jenkins
```
