import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def xor(a, b): 
    return bytes(x ^ y for x, y in zip(a, b))

def main():
    key = AESGCM.generate_key(bit_length=256)
    aes = AESGCM(key)
    
    # 2 tin nhắn bản rõ (Plaintext) giả định
    p1 = b"Chuyen khoan 1000000 VND cho An"
    p2 = b"Chuyen khoan 9999999 VND cho Bo"
    
    # Trường hợp 1: Nonce chuẩn (khác nhau)
    ok_n1, ok_n2 = os.urandom(12), os.urandom(12)
    # Trường hợp 2: Nonce LỖI (bị dùng trùng)
    bad = os.urandom(12)
    
    print("=== KIỂM THỬ DEMO HẬU QUẢ NONCE TRÙNG ===")
    for label, (n1, n2) in {"NONCE KHÁC NHAU (đúng chuẩn)": (ok_n1, ok_n2), "NONCE TRÙNG (bị lỗi)": (bad, bad)}.items():
        # Mã hóa ra bản mã (Ciphertext)
        c1, c2 = aes.encrypt(n1, p1, None), aes.encrypt(n2, p2, None)
        m = min(len(p1), len(p2))
        
        # Hacker thử XOR 2 bản mã với nhau
        leak = xor(c1[:m], c2[:m])
        truth = xor(p1[:m], p2[:m])
        
        print(f"\n== {label} ==")
        print("Kẻ tấn công tính (C1 xor C2) :", leak.hex())
        print("Thực tế của (P1 xor P2)    :", truth.hex())
        print("-> Cảnh báo: Lộ thông tin (P1 xor P2)?", leak == truth)
        
    # Kịch bản tấn công sâu hơn khi Nonce trùng
    c1, c2 = aes.encrypt(bad, p1, None), aes.encrypt(bad, p2, None)
    crib = b"Chuyen khoan "
    print("\n[TẤN CÔNG] Nếu hacker đoán được phần đầu tin nhắn 1 là:", crib)
    print("=> Sẽ tự động suy ra phần đầu tin nhắn 2 là:", xor(xor(c1[:len(crib)], c2[:len(crib)]), crib))

if __name__ == "__main__": 
    main()