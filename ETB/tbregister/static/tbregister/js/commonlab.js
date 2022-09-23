const modal = document.getElementById('modal')
const BASE_URL = 'http://46.20.206.173:18080/openmrs/ws/rest/v1'



const showModal = (uuid) => {
    console.log(uuid)
    modal.classList.remove('opacity-0')

    const url = `${BASE_URL}/commonlab/labtestattributetype`
    fetch(url,{
        method: 'GET',
        mode:'no-cors',
        headers:{
            'Accept':'application/json'
        }
    })
    .then(res=>console.log(res.body))

    
    











}



const closeModal = () => modal.classList.add('opacity-0')
    





