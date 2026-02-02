# NFS 프로비저닝 가이드

## 사전 요구사항

NFS Subdir External Provisioner를 사용하기 전에 **호스트 장비에 NFS 서버가 설치되어 있어야 합니다.**

현재 설정:
- NFS 서버 IP: `192.168.0.139`
- NFS 경로: `/srv/nfs`

## NFS 서버 설치 (Ubuntu/Debian)

### 자동 설치 (권장)

`host.sh` 스크립트를 사용하여 자동으로 NFS 서버를 설치하고 구성할 수 있습니다:

```bash
cd provisioning/nfs
sudo bash host.sh [NFS_SERVER_IP] [NETWORK_CIDR]
```

**파라미터:**
- `NFS_SERVER_IP`: NFS 서버의 IP 주소 (기본값: 자동 감지)
- `NETWORK_CIDR`: 접근 허용 네트워크 대역 (기본값: 192.168.0.0/16)

**예제:**
```bash
# 기본 설정으로 설치 (자동 IP 감지, 192.168.0.0/16 네트워크)
sudo bash host.sh

# 특정 IP와 네트워크 대역 지정
sudo bash host.sh 192.168.0.139 192.168.0.0/16

# 더 작은 네트워크 대역 지정
sudo bash host.sh 192.168.0.139 192.168.0.0/24
```

스크립트는 다음 작업을 자동으로 수행합니다:
1. NFS 서버 패키지 설치
2. `/srv/nfs` 디렉토리 생성 및 권한 설정
3. `/etc/exports` 파일에 설정 추가 (기존 설정 백업)
4. NFS 서버 재시작 및 활성화
5. 설정 확인

### 수동 설치

자동 설치를 사용하지 않는 경우 다음 단계를 따라 수동으로 설치할 수 있습니다:

#### 1. NFS 서버 패키지 설치

```bash
sudo apt update
sudo apt install -y nfs-kernel-server
```

#### 2. NFS 공유 디렉토리 생성 및 권한 설정

```bash
# 공유 디렉토리 생성
sudo mkdir -p /srv/nfs

# 권한 설정 (필요에 따라 조정)
sudo chown nobody:nogroup /srv/nfs
sudo chmod 755 /srv/nfs
```

#### 3. NFS 공유 설정

`/etc/exports` 파일에 공유 설정 추가:

```bash
sudo vi /etc/exports
```

다음 내용 추가 (Kubernetes 클러스터 노드 IP 대역에 맞게 조정):

```
/srv/nfs 192.168.0.0/16(rw,sync,no_subtree_check,no_root_squash,insecure)
```

설정 옵션 설명:
- `rw`: 읽기/쓰기 권한
- `sync`: 동기식 쓰기 (데이터 안정성 보장)
- `no_subtree_check`: 서브트리 체크 비활성화 (성능 향상)
- `no_root_squash`: root 사용자 권한 유지
- `insecure`: 비표준 포트(1024 이상) 허용 (Docker Desktop Kubernetes 등에서 필요)

**중요**: Docker Desktop Kubernetes나 일부 컨테이너 환경에서는 비표준 포트를 사용하므로 `insecure` 옵션이 필요합니다. 이 옵션이 없으면 "illegal port" 오류로 마운트가 실패할 수 있습니다.

#### 4. NFS 서버 재시작 및 상태 확인

```bash
# exports 재로드
sudo exportfs -ra

# NFS 서버 재시작
sudo systemctl restart nfs-kernel-server

# NFS 서버 상태 확인
sudo systemctl status nfs-kernel-server

# 공유 목록 확인
sudo exportfs -v
```

### 5. 방화벽 설정 (필요한 경우)

```bash
# UFW 사용 시
sudo ufw allow from 192.168.0.0/24 to any port nfs
sudo ufw reload

# 또는 iptables 사용 시
sudo iptables -A INPUT -p tcp -s 192.168.0.0/24 --dport 2049 -j ACCEPT
sudo iptables -A INPUT -p udp -s 192.168.0.0/24 --dport 2049 -j ACCEPT
```

### 6. 클라이언트에서 테스트 (선택사항)

Kubernetes 노드에서 NFS 마운트 테스트:

```bash
# 마운트 포인트 생성
sudo mkdir -p /mnt/nfs-test

# NFS 마운트
sudo mount -t nfs 192.168.0.139:/srv/nfs /mnt/nfs-test

# 마운트 확인
df -h | grep nfs

# 테스트 파일 생성
sudo touch /mnt/nfs-test/test.txt

# 언마운트
sudo umount /mnt/nfs-test
```

## 설치 순서

### 1단계: NFS 서버 설치 (호스트 서버에서)

호스트 서버에 NFS 서버를 설치합니다:

```bash
cd provisioning/nfs
sudo bash host.sh [NFS_SERVER_IP] [NETWORK_CIDR]
```

자세한 내용은 [NFS 서버 설치 (Ubuntu/Debian)](#nfs-서버-설치-ubuntudebian) 섹션을 참조하세요.

### 2단계: NFS Subdir External Provisioner 설치 (Kubernetes 클러스터에서)

NFS 서버가 준비되면 `install.sh` 스크립트를 실행하여 Kubernetes에 NFS 프로비저너를 설치합니다:

```bash
cd provisioning/nfs
bash install.sh
```

**참고**: `install.sh` 실행 전에 `values.yaml`에서 NFS 서버 IP 주소를 확인하세요.

## 문제 해결

### NFS 서버 연결 확인

```bash
# Kubernetes 노드에서 NFS 서버 접근 확인
showmount -e 192.168.0.139

# 또는
rpcinfo -p 192.168.0.139

# 포트 연결 확인
nc -zv 192.168.0.139 2049
```

### Docker Desktop Kubernetes: "illegal port" 오류

**증상**: NFS 프로비저너 Pod가 `ContainerCreating` 상태에서 `FailedMount` 오류가 발생하며 다음 메시지가 나타납니다:
```
mount.nfs: access denied by server while mounting 192.168.0.139:/srv/nfs
```

NFS 서버 로그(/var/log/syslog)에서 다음 오류를 확인할 수 있습니다:
```
refused mount request from 192.168.0.184 for /srv/nfs (/srv/nfs): illegal port 43283
```

**근본 원인**: 
- Docker Desktop Kubernetes의 kubelet이 NFS 마운트 시 비표준 포트(1024 이상, 예: 43283)를 사용합니다.
- Ubuntu NFS 서버의 기본 설정은 보안상 표준 포트(1024 미만)만 허용합니다.
- `insecure` 옵션이 없으면 `rpc.mountd`가 비표준 포트로 들어오는 마운트 요청을 거부합니다.

**해결 방법**:
1. `/etc/exports` 파일에 `insecure` 옵션 추가:
   ```
   /srv/nfs 192.168.0.0/16(rw,sync,no_subtree_check,no_root_squash,insecure)
   ```
2. NFS 서버 재시작:
   ```bash
   sudo exportfs -ra
   sudo systemctl restart nfs-kernel-server
   ```
3. Pod 재시작:
   ```bash
   kubectl delete pod -n nfs-provisioner -l app=nfs-subdir-external-provisioner
   ```

**주의사항**: `insecure` 옵션은 비표준 포트 사용을 허용하므로 신뢰할 수 있는 네트워크 환경(사설 네트워크)에서만 사용해야 합니다.

### Provisioner Pod: PVC 대신 직접 NFS 볼륨 사용

**증상**: Helm chart가 provisioner Pod의 볼륨으로 PVC를 생성하려고 시도하지만, 원하는 것은 provisioner Pod가 직접 NFS 볼륨을 사용하는 것입니다.

**해결 방법**:
- `values.yaml`에서 `persistence.enabled` 설정을 제거하거나 `false`로 설정합니다.
- `nfs.mountOptions`가 설정되어 있으면 Helm chart 템플릿이 PVC를 사용하려고 할 수 있으므로, provisioner Pod가 직접 NFS를 사용하려면 `nfs.mountOptions`를 설정하지 않거나 빈 배열로 둡니다.
- 현재 설정(`provisioning/nfs/values.yaml`)은 provisioner Pod가 직접 NFS 볼륨을 사용하도록 구성되어 있습니다.

**확인 방법**:
```bash
kubectl get deployment nfs-subdir-external-provisioner -n nfs-provisioner -o yaml | grep -A 10 "volumes:"
```
출력에서 `persistentVolumeClaim`이 아닌 `nfs:` 타입의 볼륨을 확인해야 합니다.

### NFS 프로비저너 Pod 로그 확인

```bash
kubectl logs -n nfs-provisioner -l app=nfs-subdir-external-provisioner
```

### StorageClass 확인

```bash
kubectl get storageclass nfs-client -o yaml
```

### Pod 이벤트 및 상태 확인

```bash
# Pod 상태 확인
kubectl get pods -n nfs-provisioner

# Pod 이벤트 확인 (마운트 오류 진단에 유용)
kubectl describe pod -n nfs-provisioner -l app=nfs-subdir-external-provisioner
```

## 참고 자료

- [NFS Subdir External Provisioner GitHub](https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner)
- [Ubuntu NFS Server Guide](https://ubuntu.com/server/docs/service-nfs)

