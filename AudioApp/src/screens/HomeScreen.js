import React, { useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { lessonsData } from '../data/lessonsData';

export default function HomeScreen({ navigation }) {
  const [selectedBook, setSelectedBook] = useState('book1');

  const bookOptions = [
    { value: 'book1', label: '新概念英语第一册' },
    { value: 'book2', label: '新概念英语第二册' },
    { value: 'book3', label: '新概念英语第三册' },
    { value: 'book4', label: '新概念英语第四册' },
  ];

  const currentLessons = lessonsData[selectedBook];

  const renderLessonItem = ({ item }) => (
    <TouchableOpacity
      style={styles.lessonItem}
      onPress={() => navigation.navigate('Player', { lesson: item, bookId: selectedBook })}
    >
      <View style={styles.lessonContent}>
        <Text style={styles.lessonTitle}>{item.title}</Text>
        <Text style={styles.lessonTitleCn}>{item.titleCn}</Text>
      </View>
      <Text style={styles.arrow}>›</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#2196F3" />

      {/* 书籍选择器 */}
      <View style={styles.pickerContainer}>
        <Picker
          selectedValue={selectedBook}
          onValueChange={(itemValue) => setSelectedBook(itemValue)}
          style={styles.picker}
        >
          {bookOptions.map((option) => (
            <Picker.Item
              key={option.value}
              label={option.label}
              value={option.value}
            />
          ))}
        </Picker>
      </View>

      {/* 课文列表 */}
      <FlatList
        data={currentLessons}
        renderItem={renderLessonItem}
        keyExtractor={(item) => `${selectedBook}-${item.id}`}
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
  pickerContainer: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  picker: {
    height: 50,
  },
  listContent: {
    paddingVertical: 8,
  },
  lessonItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 16,
    marginHorizontal: 8,
    marginVertical: 4,
    borderRadius: 8,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  lessonContent: {
    flex: 1,
  },
  lessonTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  lessonTitleCn: {
    fontSize: 14,
    color: '#666',
  },
  arrow: {
    fontSize: 24,
    color: '#2196F3',
    marginLeft: 8,
  },
  separator: {
    height: 4,
  },
});
