import api from './axios';

// URL: ://service/api/authors/{AUTHOR_SERIAL}/posts/{POST_SERIAL}
export const getPost = async (authorSerial, postSerial) => {
  try {
    const response = await api.get(
      `/authors/${authorSerial}/posts/${postSerial}`
    );
    return response.data;
  } catch (error) {
    console.error(error);
  }
};
export const deletePost = async (authorSerial, postSerial) => {
  try {
    const response = await api.delete(
      `/authors/${authorSerial}/posts/${postSerial}`
    );
    return response.data;
  } catch (error) {
    console.error(error);
  }
};
export const updatePost = async (authorSerial, postSerial, postData) => {
  try {
    const response = await api.put(
      `/authors/${authorSerial}/posts/${postSerial}`,
      postData
    );
    return response.data;
  } catch (error) {
    console.error(error);
  }
};

// URL: ://service/api/posts/{POST_FQID}
export const getPostByFqid = async (postFqid) => {
  try {
    const response = await api.get(`/posts/${postFqid}`);
    return response.data;
  } catch (error) {
    console.error(error);
  }
};

// URL: ://service/api/authors/{AUTHOR_SERIAL}/posts/
export const getAllPosts = async (authorSerial) => {
  try {
    const response = await api.get(`/authors/${authorSerial}/posts`);
    return response.data;
  } catch (error) {
    console.error(error);
  }
};
export const createPost = async (authorSerial, postData) => {
  try {
    const response = await api.post(`/authors/${authorSerial}/posts`, postData);
    return response.data;
  } catch (error) {
    console.error(error);
  }
};

// URL: ://service/api/authors/{AUTHOR_SERIAL}/posts/{POST_SERIAL}/image
export const getPostImage = async (authorSerial, postSerial) => {
  try {
    const response = await api.get(
      `/authors/${authorSerial}/posts/${postSerial}/image`
    );
    return response.data;
  } catch (error) {
    console.error(error);
  }
};