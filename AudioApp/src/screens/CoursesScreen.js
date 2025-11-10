import React from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Image,
  StatusBar,
} from 'react-native';
import { booksInfo } from '../data/lessonsData';

export default function CoursesScreen({ navigation }) {
  const renderBookItem = ({ item }) => (
    <TouchableOpacity
      style={styles.bookCard}
      onPress={() => navigation.navigate('Home', { selectedBook: item.id })}
    >
      <View style={styles.bookImageContainer}>
        <View style={styles.bookImagePlaceholder}>
          <Text style={styles.bookImageText}>{item.title.substring(0, 2)}</Text>
        </View>
      </View>
      <View style={styles.bookInfo}>
        <Text style={styles.bookTitle}>{item.title}</Text>
        <Text style={styles.bookSubtitle}>{item.subtitle}</Text>
        <Text style={styles.bookDescription}>{item.description}</Text>
        <View style={styles.bookMeta}>
          <Text style={styles.lessonCount}>共 {item.lessons} 课</Text>
        </View>
      </View>
      <Text style={styles.arrow}>›</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#2196F3" />

      <View style={styles.header}>
        <Text style={styles.headerTitle}>选择课程</Text>
        <Text style={styles.headerSubtitle}>New Concept English</Text>
      </View>

      <FlatList
        data={booksInfo}
        renderItem={renderBookItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#999',
    marginTop: 4,
  },
  listContent: {
    padding: 12,
  },
  bookCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  bookImageContainer: {
    marginRight: 16,
  },
  bookImagePlaceholder: {
    width: 80,
    height: 100,
    backgroundColor: '#2196F3',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  bookImageText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  bookInfo: {
    flex: 1,
    justifyContent: 'center',
  },
  bookTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  bookSubtitle: {
    fontSize: 13,
    color: '#2196F3',
    marginBottom: 4,
    fontStyle: 'italic',
  },
  bookDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  bookMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  lessonCount: {
    fontSize: 12,
    color: '#999',
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  arrow: {
    fontSize: 32,
    color: '#2196F3',
    alignSelf: 'center',
  },
  separator: {
    height: 8,
  },
});
