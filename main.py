<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Web3 Wallet Dashboard</title>

<script src="https://unpkg.com/ethers@5.7.2/dist/ethers.umd.min.js"></script>
<script src="https://unpkg.com/@walletconnect/ethereum-provider@2.11.0/dist/index.umd.min.js"></script>

<style>
body{
  margin:0;
  font-family:Arial;
  background:linear-gradient(-45deg,#0f2027,#203a43,#2c5364,#000);
  background-size:400% 400%;
  animation:gradient 12s ease infinite;
  color:white;
  text-align:center;
  padding-top:80px;
}
@keyframes gradient{
  0%{background-position:0% 50%}
  50%{background-position:100% 50%}
  100%{background-position:0% 50%}
}
.container{
  background:rgba(0,0,0,0.65);
  padding:30px;
  border-radius:20px;
  width:360px;
  margin:auto;
  box-shadow:0 0 25px rgba(0,255,255,0.4);
}
button{
  padding:14px 28px;
  border:none;
  border-radius:30px;
  font-size:15px;
  cursor:pointer;
  background:linear-gradient(90deg,#00f2fe,#4facfe);
  color:white;
  font-weight:bold;
  margin:8px;
  transition:.3s;
}
button:hover{
  transform:scale(1.05);
  box-shadow:0 0 15px #00f2fe;
}
.balance{
  margin-top:15px;
  font-size:16px;
  word-break:break-all;
}
</style>
</head>

<body>

<div class="container">
  <h2>Web3 Wallet Dashboard</h2>
  <button onclick="connectWallet()">Connect Wallet</button>

  <div class="balance" id="address">Address: -</div>
  <div class="balance" id="eth">ETH: -</div>
  <div class="balance" id="bnb">BNB: -</div>
</div>

<script>
let userAddress;
const projectId = "ff0cecca30909c612e7cfc06e8b4c664";

async function connectWallet(){
  try{

    // Force WalletConnect only (no injected detection)
    const EthereumProvider = window.WalletConnectEthereumProvider || window.EthereumProvider;

    if(!EthereumProvider){
      alert("WalletConnect library failed to load. Try different hosting (Netlify recommended).");
      return;
    }

    const provider = await EthereumProvider.init({
      projectId: projectId,
      chains: [1,56],
      showQrModal: true,
      rpcMap:{
        1:"https://rpc.walletconnect.org/v1?chainId=eip155:1&projectId="+projectId,
        56:"https://rpc.walletconnect.org/v1?chainId=eip155:56&projectId="+projectId
      }
    });

    await provider.enable();

    const ethersProvider = new ethers.providers.Web3Provider(provider);
    const signer = ethersProvider.getSigner();
    userAddress = await signer.getAddress();

    document.getElementById("address").innerText = "Address: " + userAddress;

    loadBalances();

  }catch(err){
    alert("Connection failed: " + err.message);
    console.error(err);
  }
}

async function loadBalances(){

  const ethProvider = new ethers.providers.JsonRpcProvider(
    "https://rpc.walletconnect.org/v1?chainId=eip155:1&projectId="+projectId
  );
  const ethBalance = await ethProvider.getBalance(userAddress);
  document.getElementById("eth").innerText =
    "ETH: " + parseFloat(
      ethers.utils.formatEther(ethBalance)
    ).toFixed(4);

  const bnbProvider = new ethers.providers.JsonRpcProvider(
    "https://rpc.walletconnect.org/v1?chainId=eip155:56&projectId="+projectId
  );
  const bnbBalance = await bnbProvider.getBalance(userAddress);
  document.getElementById("bnb").innerText =
    "BNB: " + parseFloat(
      ethers.utils.formatEther(bnbBalance)
    ).toFixed(4);
}
</script>

</body>
</html>