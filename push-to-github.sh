#!/bin/bash
# JingUninstall 推送到 GitHub 脚本

echo "======================================"
echo "  推送到 GitHub"
echo "======================================"
echo ""

cd /home/jinkang/桌面/造梦空间/JingUninstall

# 设置远程仓库
git remote set-url origin https://github.com/jinkang19940922/jing-uninstall.git

echo "正在推送代码到 GitHub..."
echo "提示：需要输入 GitHub 用户名和密码（或个人访问令牌）"
echo ""

# 推送代码
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 代码推送成功！"
    echo ""
    echo "正在推送版本标签..."
    git push origin --tags
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ 标签推送成功！"
        echo ""
        echo "======================================"
        echo "  完成！"
        echo "======================================"
        echo ""
        echo "请访问你的 GitHub 仓库："
        echo "https://github.com/jinkang19940922/jing-uninstall"
        echo ""
        echo "创建 Release 步骤："
        echo "1. 访问仓库页面"
        echo "2. 点击 Releases -> Create a new release"
        echo "3. 选择标签 v1.0.0"
        echo "4. 上传 jing-uninstall_1.0.0_all.deb 文件"
        echo "5. 点击 Publish release"
    else
        echo "❌ 标签推送失败，请手动执行：git push origin --tags"
    fi
else
    echo ""
    echo "❌ 推送失败，请检查："
    echo "1. GitHub 用户名和密码是否正确"
    echo "2. 仓库是否存在"
    echo "3. 是否有访问权限"
    echo ""
    echo "建议使用个人访问令牌代替密码："
    echo "https://github.com/settings/tokens"
fi
